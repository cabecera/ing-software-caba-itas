from django.http import HttpResponse
from django.template import loader
from django.db import connection, DatabaseError, OperationalError
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db.utils import DatabaseError as DjangoDatabaseError
import os
import sqlite3


class DatabaseCheckMiddleware:
    """
    Middleware que verifica la conexión a la base de datos
    y muestra un error amigable si no está disponible
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar que el archivo de base de datos existe (para SQLite)
        db_path = settings.DATABASES['default']['NAME']
        if isinstance(db_path, str):
            db_file = db_path
        else:
            db_file = str(db_path)

        # Verificar si el archivo existe
        if not os.path.exists(db_file):
            template = loader.get_template('error_base_datos.html')
            return HttpResponse(
                template.render({
                    'error': f'El archivo de base de datos no existe: {db_file}',
                    'mensaje': 'La base de datos no está disponible. El archivo db.sqlite3 no se encuentra en la raíz del proyecto.'
                }),
                status=503
            )

        # Verificar conexión a la base de datos y que tenga las tablas necesarias
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                # Verificar que existan las tablas básicas de Django
                try:
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table' AND name='django_session'
                    """)
                    if not cursor.fetchone():
                        # La base de datos existe pero está vacía o no tiene tablas
                        raise OperationalError("La base de datos no tiene las tablas necesarias. Ejecuta: python manage.py migrate")
                except (sqlite3.OperationalError, OperationalError) as table_error:
                    # Si falla al verificar la tabla, la BD está vacía
                    error_msg = str(table_error)
                    if "no such table" in error_msg.lower():
                        raise OperationalError("La base de datos está vacía. Ejecuta: python manage.py migrate")
                    raise
        except (DatabaseError, OperationalError, DjangoDatabaseError, sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            # Si hay error de conexión o tablas faltantes, mostrar página de error
            error_msg = str(e)
            if "no such table" in error_msg.lower() or "no tiene las tablas" in error_msg:
                mensaje = 'La base de datos está vacía o no tiene las tablas necesarias. Ejecuta: python manage.py migrate'
            else:
                mensaje = 'La base de datos no está disponible o no está conectada. Verifica que el archivo db.sqlite3 exista y tenga los permisos correctos.'

            template = loader.get_template('error_base_datos.html')
            return HttpResponse(
                template.render({
                    'error': error_msg,
                    'mensaje': mensaje
                }),
                status=503
            )
        except Exception as e:
            # Cualquier otro error relacionado con la base de datos
            template = loader.get_template('error_base_datos.html')
            return HttpResponse(
                template.render({
                    'error': str(e),
                    'mensaje': 'Error al conectar con la base de datos.'
                }),
                status=503
            )

        # Si todo está bien, continuar con la request
        try:
            response = self.get_response(request)
            return response
        except (DatabaseError, OperationalError, DjangoDatabaseError, sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            # Si ocurre un error de BD durante el procesamiento de la request
            error_msg = str(e)
            if "no such table" in error_msg.lower():
                mensaje = 'La base de datos está vacía o no tiene las tablas necesarias. Ejecuta: python manage.py migrate'
            elif "database is locked" in error_msg.lower():
                mensaje = 'La base de datos está bloqueada. Asegúrate de que no haya otro proceso usando el archivo.'
            else:
                mensaje = 'Error al acceder a la base de datos durante el procesamiento de la solicitud.'

            template = loader.get_template('error_base_datos.html')
            return HttpResponse(
                template.render({
                    'error': error_msg,
                    'mensaje': mensaje
                }),
                status=503
            )
        except Exception as e:
            # Capturar cualquier otro error relacionado con BD que pueda ocurrir
            error_msg = str(e)
            # Verificar si es un error de base de datos
            if any(keyword in error_msg.lower() for keyword in ["no such table", "database", "sqlite", "operationalerror"]):
                template = loader.get_template('error_base_datos.html')
                return HttpResponse(
                    template.render({
                        'error': error_msg,
                        'mensaje': 'Error de base de datos detectado. La base de datos está vacía o no tiene las tablas necesarias. Ejecuta: python manage.py migrate'
                    }),
                    status=503
                )
            # Si no es un error de BD, re-lanzar la excepción
            raise

