from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import connection
from gestion.models import Cliente, Cabaña, Implemento
from datetime import date


class Command(BaseCommand):
    help = 'Inicializa datos básicos del sistema (usuarios, cabañas, implementos, grupos)'

    def check_tables_exist(self):
        """Verifica si las tablas de la base de datos existen"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE 'gestion_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            return len(tables) > 0

    def handle(self, *args, **options):
        # Verificar que las migraciones estén aplicadas
        if not self.check_tables_exist():
            self.stdout.write(self.style.ERROR(
                '\n❌ Error: Las tablas de la base de datos no existen.\n'
                'Por favor ejecuta primero:\n'
                '  python manage.py makemigrations\n'
                '  python manage.py migrate\n'
            ))
            return
        # Crear grupo de Encargados
        grupo_encargados, created = Group.objects.get_or_create(name='Encargados')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Encargados" creado'))
        else:
            self.stdout.write(self.style.WARNING('Grupo "Encargados" ya existe'))

        # Crear usuario administrador
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@cabanitas.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Usuario administrador creado (usuario: admin, contraseña: admin123)'))
        else:
            self.stdout.write(self.style.WARNING('Usuario administrador ya existe'))

        # Crear usuario encargado
        encargado_user, created = User.objects.get_or_create(
            username='encargado',
            defaults={
                'email': 'encargado@cabanitas.com',
                'first_name': 'Encargado',
                'last_name': 'Sistema',
                'is_staff': False
            }
        )
        if created:
            encargado_user.set_password('encargado123')
            encargado_user.save()
            encargado_user.groups.add(grupo_encargados)
            self.stdout.write(self.style.SUCCESS('Usuario encargado creado (usuario: encargado, contraseña: encargado123)'))
        else:
            # Asegurar que esté en el grupo
            if not encargado_user.groups.filter(name='Encargados').exists():
                encargado_user.groups.add(grupo_encargados)
            self.stdout.write(self.style.WARNING('Usuario encargado ya existe'))

        # Crear cliente de ejemplo
        try:
            cliente_user, created = User.objects.get_or_create(
                username='cliente',
                defaults={
                    'email': 'cliente@ejemplo.com',
                    'first_name': 'Juan',
                    'last_name': 'Pérez'
                }
            )
            if created:
                cliente_user.set_password('cliente123')
                cliente_user.save()
                Cliente.objects.get_or_create(
                    usuario=cliente_user,
                    defaults={
                        'nombre': 'Juan Pérez',
                        'telefono': '+56912345678',
                        'email': 'cliente@ejemplo.com',
                        'direccion': 'Calle Ejemplo 123',
                        'tipoCliente': 'Regular'
                    }
                )
                self.stdout.write(self.style.SUCCESS('Cliente de ejemplo creado (usuario: cliente, contraseña: cliente123)'))
            else:
                # Verificar si ya tiene perfil de cliente
                if not hasattr(cliente_user, 'cliente'):
                    Cliente.objects.get_or_create(
                        usuario=cliente_user,
                        defaults={
                            'nombre': 'Juan Pérez',
                            'telefono': '+56912345678',
                            'email': 'cliente@ejemplo.com',
                            'direccion': 'Calle Ejemplo 123',
                            'tipoCliente': 'Regular'
                        }
                    )
                self.stdout.write(self.style.WARNING('Cliente de ejemplo ya existe'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear cliente: {e}'))

        # Crear cabañas de ejemplo
        cabañas_data = [
            {'nombre': 'Cabaña del Bosque', 'capacidad': 4, 'precioNoche': 50000, 'estado': 'lista'},
            {'nombre': 'Cabaña del Lago', 'capacidad': 6, 'precioNoche': 75000, 'estado': 'lista'},
            {'nombre': 'Cabaña Familiar', 'capacidad': 8, 'precioNoche': 100000, 'estado': 'lista'},
            {'nombre': 'Cabaña Rústica', 'capacidad': 2, 'precioNoche': 35000, 'estado': 'lista'},
        ]

        for cab_data in cabañas_data:
            cabaña, created = Cabaña.objects.get_or_create(
                nombre=cab_data['nombre'],
                defaults={
                    'capacidad': cab_data['capacidad'],
                    'precioNoche': cab_data['precioNoche'],
                    'estado': cab_data['estado']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Cabaña "{cabaña.nombre}" creada'))
            else:
                self.stdout.write(self.style.WARNING(f'Cabaña "{cabaña.nombre}" ya existe'))

        # Crear implementos de ejemplo
        implementos_data = [
            {'nombre': 'Parillas', 'descripcion': 'Parillas para asados', 'cantidadTotal': 5, 'cantidadDisponible': 5},
            {'nombre': 'Sillas de Playa', 'descripcion': 'Sillas plegables para playa', 'cantidadTotal': 20, 'cantidadDisponible': 20},
            {'nombre': 'Mesa Plegable', 'descripcion': 'Mesas plegables para exteriores', 'cantidadTotal': 10, 'cantidadDisponible': 10},
            {'nombre': 'Cooler', 'descripcion': 'Coolers para mantener alimentos fríos', 'cantidadTotal': 8, 'cantidadDisponible': 8},
            {'nombre': 'Kayak', 'descripcion': 'Kayaks para uso en el lago', 'cantidadTotal': 4, 'cantidadDisponible': 4},
        ]

        for imp_data in implementos_data:
            implemento, created = Implemento.objects.get_or_create(
                nombre=imp_data['nombre'],
                defaults={
                    'descripcion': imp_data['descripcion'],
                    'cantidadTotal': imp_data['cantidadTotal'],
                    'cantidadDisponible': imp_data['cantidadDisponible'],
                    'estado': 'disponible'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Implemento "{implemento.nombre}" creado'))
            else:
                self.stdout.write(self.style.WARNING(f'Implemento "{implemento.nombre}" ya existe'))

        self.stdout.write(self.style.SUCCESS('\n¡Datos iniciales creados exitosamente!'))
        self.stdout.write(self.style.SUCCESS('Puedes crear un superusuario con: python manage.py createsuperuser'))

