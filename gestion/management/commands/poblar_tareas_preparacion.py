from django.core.management.base import BaseCommand
from gestion.models import TareaPreparacion


class Command(BaseCommand):
    help = 'Pobla las tareas estándar de preparación de cabañas'

    def handle(self, *args, **options):
        tareas_base = [
            {'categoria': 'limpieza', 'nombre': 'Limpiar', 'orden': 1,
             'descripcion': 'Limpieza general de la cabaña'},

            {'categoria': 'inventario', 'nombre': 'Reponer', 'orden': 2,
             'descripcion': 'Reponer suministros y verificar inventario'},

            {'categoria': 'mantenimiento', 'nombre': 'Verificar funcionamiento', 'orden': 3,
             'descripcion': 'Revisar que todo funcione correctamente'},

            {'categoria': 'exteriores', 'nombre': 'Preparar exteriores', 'orden': 4,
             'descripcion': 'Limpiar y ordenar áreas exteriores'},

            {'categoria': 'seguridad', 'nombre': 'Verificar cerraduras', 'orden': 5,
             'descripcion': 'Revisar cerraduras, llaves y seguridad'},
        ]

        total_creadas = 0
        total_existentes = 0

        for tarea_data in tareas_base:
            tarea, created = TareaPreparacion.objects.get_or_create(
                nombre=tarea_data['nombre'],
                defaults={
                    'categoria': tarea_data['categoria'],
                    'orden': tarea_data['orden'],
                    'descripcion': tarea_data.get('descripcion', 'Tarea estándar de preparación de cabañas'),
                    'es_obligatoria': True
                }
            )
            if created:
                total_creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {tarea.get_categoria_display()} - {tarea.nombre}'))
            else:
                total_existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nProceso completado:\n'
            f'  - Tareas creadas: {total_creadas}\n'
            f'  - Tareas ya existentes: {total_existentes}\n'
            f'  - Total procesado: {total_creadas + total_existentes}'
        ))

