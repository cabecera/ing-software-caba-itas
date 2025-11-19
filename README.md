# Sistema de Gestión "Las Cabañitas"

Sistema web completo para la gestión de reservas, inventario, mantenimiento y encuestas de satisfacción del emprendimiento familiar "Las Cabañitas".

## Inicio Rápido

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar base de datos (IMPORTANTE: hacer esto primero)**:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Crear datos iniciales (incluye usuarios de ejemplo)**:
```bash
python manage.py init_data
```

Ejecutar migracioenes antes de `init_data` si no, tendriamos un error

Esto crea automáticamente:
- Usuario **admin** (contraseña: `admin123`) - Administrador
- Usuario **encargado** (contraseña: `encargado123`) - Encargado
- Usuario **cliente** (contraseña: `cliente123`) - Cliente de ejemplo
- Cabañas e implementos de ejemplo

4. **Ejecutar servidor**:
```bash
python manage.py runserver
```

**Nota**: Si quieres crear tu propio superusuario adicional, puedes hacerlo con:
```bash
python manage.py createsuperuser
```

### Acceder al sistema

- **URL principal**: http://127.0.0.1:8000/
- **Admin Django**: http://127.0.0.1:8000/admin/
- **Dashboard Administrador**: http://127.0.0.1:8000/administrador/dashboard/
- **Dashboard Encargado**: http://127.0.0.1:8000/encargado/dashboard/
- **Portal Cliente**: http://127.0.0.1:8000/cliente/

## Roles del Sistema

- **Cliente**: Solicita reservas, completa encuestas, solicita préstamos
- **Encargado**: Gestiona inventario, mantenimientos, préstamos
- **Administrador**: Acceso completo, gestión de reservas, pagos, reportes

## Documentación

Ver `documentacion.md` para documentación completa del sistema.

## Tecnologías

- Django 4.x
- Python 3.8+
- SQLite (desarrollo)
- HTML5, CSS3, JavaScript vanilla

## Estructura del Proyecto

```
cabaña/
├── gestion/            # Aplicación principal
│   ├── templates/      # Plantillas HTML
│   ├── static/         # Archivos estáticos (CSS)
│   │   └── css/
│   │       └── style.css
│   ├── models.py
│   ├── views.py
│   └── ...
├── cabanitas/          # Configuración del proyecto
└── manage.py
```

## Notas

- El sistema está diseñado para ser simple pero funcional
- Los colores y estilos siguen una estética rural/natural
- Responsive design para móviles y tablets
- CSS centralizado en `gestion/static/css/style.css` (sin estilos inline)
- Templates y static dentro de la app `gestion/` siguiendo estructura Django estándar

