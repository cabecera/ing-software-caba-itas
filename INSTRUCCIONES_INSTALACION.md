
---------------------------------------
## 1. Instalar dependencias
pip install -r requirements.txt

## 2. Crear base de datos
python manage.py migrate

## 3. Crear datos iniciales (usuarios, cabañas, implementos)
python manage.py init_data

## 4. Poblar checklist de inventario
python manage.py poblar_checklist

## 5. Poblar tareas de preparación
python manage.py poblar_tareas_preparacion

## 6. Ejecutar servidor
python manage.py runserver


Credenciales de acceso (creadas por init_data):
Rol		Usuario			Contraseña
Administrador	admin			admin123
Encargado	encargado		encargado123
Cliente		cliente			cliente123