from django.core.management.base import BaseCommand
from gestion.models import Cabaña, ChecklistInventario


class Command(BaseCommand):
    help = 'Pobla el checklist de inventario base para todas las cabañas'

    def handle(self, *args, **options):
        cabañas = Cabaña.objects.all()

        if not cabañas.exists():
            self.stdout.write(self.style.WARNING(
                'No hay cabañas registradas. Ejecuta primero: python manage.py init_data'
            ))
            return

        items_base = [
            # COCINA
            {'categoria': 'cocina', 'nombre_item': 'Refrigerador', 'cantidad_esperada': 1, 'precio_reposicion': 150000, 'orden': 1},
            {'categoria': 'cocina', 'nombre_item': 'Cocina a gas', 'cantidad_esperada': 1, 'precio_reposicion': 80000, 'orden': 2},
            {'categoria': 'cocina', 'nombre_item': 'Microondas', 'cantidad_esperada': 1, 'precio_reposicion': 60000, 'orden': 3},
            {'categoria': 'cocina', 'nombre_item': 'Hervidor', 'cantidad_esperada': 1, 'precio_reposicion': 25000, 'orden': 4},
            {'categoria': 'cocina', 'nombre_item': 'Juego de loza(6 personas)', 'cantidad_esperada': 1, 'precio_reposicion': 30000, 'orden': 5},
            {'categoria': 'cocina', 'nombre_item': 'Juego de cubiertos (6 personas)', 'cantidad_esperada': 1, 'precio_reposicion': 20000, 'orden': 6},
            {'categoria': 'cocina', 'nombre_item': 'Ollas y sartenes', 'cantidad_esperada': 1, 'precio_reposicion': 40000, 'orden': 7},


            # BAÑO
            {'categoria': 'baño', 'nombre_item': 'Toallas de baño', 'cantidad_esperada': 6, 'precio_reposicion': 10000, 'orden': 30},

        ]

        total_creados = 0
        total_existentes = 0

        for cabaña in cabañas:
            self.stdout.write(f'\nProcesando {cabaña.nombre}...')
            for item_data in items_base:
                item, created = ChecklistInventario.objects.get_or_create(
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
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {item.nombre_item}'))
                else:
                    total_existentes += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nProceso completado:\n'
            f'  - Items creados: {total_creados}\n'
            f'  - Items ya existentes: {total_existentes}\n'
            f'  - Total procesado: {total_creados + total_existentes}'
        ))

