from django.core.management.base import BaseCommand
from gestion.models import Cabaña, ChecklistInventario


class Command(BaseCommand):
    help = 'Pobla el checklist de inventario para todas las cabañas con items básicos'

    def handle(self, *args, **options):
        # Obtener todas las cabañas
        cabañas = Cabaña.objects.all()

        if not cabañas.exists():
            self.stdout.write(self.style.WARNING('No hay cabañas en la base de datos. Ejecuta primero: python manage.py init_data'))
            return

        # Items básicos del checklist (solo 5)
        items_base = [
            {'categoria': 'cocina', 'nombre_item': 'Vajilla completa', 'cantidad_esperada': 1, 'precio_reposicion': 30000, 'orden': 1},
            {'categoria': 'baño', 'nombre_item': 'Toallas', 'cantidad_esperada': 4, 'precio_reposicion': 10000, 'orden': 2},
            {'categoria': 'dormitorio', 'nombre_item': 'Sábanas', 'cantidad_esperada': 2, 'precio_reposicion': 15000, 'orden': 3},
            {'categoria': 'cocina', 'nombre_item': 'Tetera', 'cantidad_esperada': 1, 'precio_reposicion': 25000, 'orden': 4},
            {'categoria': 'otros', 'nombre_item': 'Mesa y sillas', 'cantidad_esperada': 1, 'precio_reposicion': 50000, 'orden': 5},
        ]

        total_creados = 0
        total_actualizados = 0

        for cabaña in cabañas:
            self.stdout.write(f'Procesando {cabaña.nombre}...')

            for item_data in items_base:
                item, created = ChecklistInventario.objects.update_or_create(
                    cabaña=cabaña,
                    nombre_item=item_data['nombre_item'],
                    defaults={
                        'categoria': item_data['categoria'],
                        'cantidad_esperada': item_data['cantidad_esperada'],
                        'precio_reposicion': item_data['precio_reposicion'],
                        'orden': item_data['orden'],
                        'es_obligatorio': True
                    }
                )

                if created:
                    total_creados += 1
                    self.stdout.write(f'  ✓ Creado: {item.nombre_item}')
                else:
                    total_actualizados += 1
                    self.stdout.write(f'  ↻ Actualizado: {item.nombre_item}')

        self.stdout.write(self.style.SUCCESS(
            f'\nChecklist completado!\n'
            f'   Items creados: {total_creados}\n'
            f'   Items actualizados: {total_actualizados}\n'
            f'   Total items por cabaña: {len(items_base)}'
        ))
