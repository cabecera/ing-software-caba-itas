from django.core.management.base import BaseCommand
from gestion.models import TareaPreparacion


class Command(BaseCommand):
    help = 'Pobla las tareas estándar de preparación de cabañas'

    def handle(self, *args, **options):
        # Tareas de preparación (actividades que el encargado realiza)
        # NOTA: El control de inventario (vajilla, toallas, sábanas, etc.) se hace con el ChecklistInventario
        # que se verifica en la sección "Verificación de Inventario" durante la preparación
        tareas = [
            {
                'categoria': 'limpieza',
                'nombre': 'Limpieza general de la cabaña',
                'descripcion': 'Limpieza completa de todas las áreas: pisos, superficies, baños, cocina, dormitorios y áreas comunes.',
                'orden': 1
            },
            {
                'categoria': 'mantenimiento',
                'nombre': 'Revisión de electrodomésticos',
                'descripcion': 'Verificar funcionamiento de refrigerador, cocina, microondas, tetera y otros electrodomésticos.',
                'orden': 2
            },
            {
                'categoria': 'mantenimiento',
                'nombre': 'Mantención de estufas',
                'descripcion': 'Revisar y limpiar estufas, verificar funcionamiento y seguridad.',
                'orden': 3
            },
            {
                'categoria': 'exteriores',
                'nombre': 'Llenado de leñera (solo en invierno)',
                'descripcion': 'Verificar y llenar la leñera con leña suficiente para la estadía. Solo aplica en temporada de invierno.',
                'orden': 4
            },
        ]

        total_creados = 0
        total_actualizados = 0

        for tarea_data in tareas:
            tarea, created = TareaPreparacion.objects.update_or_create(
                nombre=tarea_data['nombre'],
                defaults={
                    'categoria': tarea_data['categoria'],
                    'descripcion': tarea_data['descripcion'],
                    'orden': tarea_data['orden'],
                    'es_obligatoria': True
                }
            )

            if created:
                total_creados += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Creada: {tarea.nombre}'))
            else:
                total_actualizados += 1
                self.stdout.write(f'  ↻ Actualizada: {tarea.nombre}')

        self.stdout.write(self.style.SUCCESS(
            f'\nTareas de preparación completadas!\n'
            f'   Tareas creadas: {total_creados}\n'
            f'   Tareas actualizadas: {total_actualizados}\n'
            f'   Total: {len(tareas)} tareas'
        ))
