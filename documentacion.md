# Documentación del Sistema "Las Cabañitas"

## Descripción General

Sistema web completo de gestión para el emprendimiento familiar "Las Cabañitas" que automatiza reservas, inventario, mantenimiento y encuestas de satisfacción. El sistema está desarrollado con Django 4.x y sigue el patrón MVT (Model-View-Template).

### Características Principales

-  **CSS Centralizado**: Todo el CSS está en `gestion/static/css/style.css` (sin estilos inline)
- **Templates Organizados**: Templates dentro de `gestion/templates/` siguiendo estructura Django estándar
- **Usuarios de Ejemplo**: Sistema crea automáticamente usuarios de prueba (admin, encargado, cliente)
- **Diseño Simple**: Interfaz funcional con estética rural/natural

## Arquitectura del Sistema

### Stack Tecnológico

- **Backend**: Django 4.x con Python 3.8+
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Autenticación**: Sistema de grupos nativo de Django
- **Archivos estáticos**: Whitenoise para servir CSS/JS
- **CSS**: Centralizado en `gestion/static/css/style.css` (sin estilos inline en HTML)

### Estructura del Proyecto

```
cabaña/
├── cabanitas/          # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── gestion/            # Aplicación principal
│   ├── models.py       # Modelos de datos
│   ├── views.py        # Vistas y lógica de negocio
│   ├── forms.py        # Formularios
│   ├── urls.py         # Rutas de la aplicación
│   ├── admin.py        # Configuración del admin
│   ├── decorators.py   # Decoradores de permisos
│   ├── templates/      # Plantillas HTML
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── cliente/    # Templates del módulo cliente
│   │   ├── admin/      # Templates del módulo administrador
│   │   └── encargado/  # Templates del módulo encargado
│   └── static/         # Archivos estáticos (CSS, JS, imágenes)
│       └── css/
│           └── style.css
├── media/              # Archivos subidos por usuarios
├── manage.py
├── requirements.txt
└── documentacion.md
```

## Modelos de Datos

### Entidades Principales

#### Cliente
- **Campos**: idCliente, nombre, telefono, email, direccion, tipoCliente
- **Relaciones**: 1:N con Reserva, 1:1 con User (Django)
- **Métodos**: solicitarReserva(), confirmarReserva(), completarEncuesta()

#### Reserva
- **Campos**: idReserva, fechaInicio, fechaFin, numPersonas, estado, montoCotizado, comentarios
- **Relaciones**: N:1 con Cliente y Cabaña, 1:1 con Encuesta, 1:N con Pago y PrestamoImplemento
- **Estados**: pendiente, confirmada, cancelada, completada
- **Métodos**: registrarReserva(), actualizarReserva(), confirmarReserva(), generarAlerta(), enviarNotificacionPreparacion()

#### Cabaña
- **Campos**: idCabaña, nombre, capacidad, estado, precioNoche
- **Relaciones**: 1:N con Reserva y Mantenimiento
- **Estados**: disponible, ocupada, mantenimiento, reservada

#### Encuesta
- **Campos**: idEncuesta, calificacion (1-5), comentarios, fecha
- **Relaciones**: 1:1 con Reserva

#### Pago
- **Campos**: idPago, monto, metodo, fechaPago, comprobante
- **Relaciones**: N:1 con Reserva
- **Métodos**: registrarPago(), actualizarComprobante()

#### Implemento
- **Campos**: idImplemento, nombre, descripcion, cantidadTotal, cantidadDisponible, estado
- **Relaciones**: 1:N con PrestamoImplemento
- **Métodos**: actualizarDisponibilidad(), registrarPrestamo()

#### PrestamoImplemento
- **Campos**: idPrestamo, fechaPrestamo, fechaDevolucion, cantidad, devuelto
- **Relaciones**: N:1 con Reserva e Implemento
- **Métodos**: registrarPrestamo(), registrarDevolucion()

#### Mantenimiento
- **Campos**: idMantenimiento, tipo, descripcion, fechaProgramada, fechaEjecucion, estado
- **Relaciones**: N:1 con Cabaña
- **Tipos**: preventivo, correctivo, limpieza, reparacion
- **Estados**: programado, en_proceso, completado, cancelado
- **Métodos**: registrarMantenimiento(), finalizarMantenimiento(), programarMantenimiento()

#### Notificacion
- **Campos**: idNotificacion, tipo, mensaje, fechaEnvio, leida
- **Relaciones**: N:1 con User (Django)
- **Tipos**: alerta, confirmacion, preparacion, recordatorio, general
- **Métodos**: enviar(), marcarLeida()

### Notas sobre Relaciones

**Resolución de relaciones implementadas:**
- Se utilizó el modelo User de Django en lugar de crear un modelo Usuario separado, ya que Django ya proporciona autenticación y gestión de usuarios.
- Cliente tiene una relación OneToOne con User para vincular cuentas de usuario con perfiles de cliente.
- Las relaciones entre modelos siguen el diagrama de clases proporcionado, manteniendo la integridad referencial.

## 👥 Sistema de Roles y Permisos

### Roles Implementados

#### 1. Cliente
- **Acceso**: Portal personal, solicitar reservas, ver sus reservas, completar encuestas, solicitar préstamos
- **Restricciones**: Solo ve información propia
- **Decorador**: `@cliente_required`

#### 2. Encargado
- **Acceso**: Gestión de inventario, mantenimientos, préstamos, estado de cabañas, preparación
- **Restricciones**: No accede a datos financieros
- **Decorador**: `@encargado_required`
- **Grupo Django**: "Encargados"

#### 3. Administrador
- **Acceso**: Completo al sistema
- **Funciones**: Gestión de reservas, pagos, reportes, clientes, encuestas, supervisión
- **Decorador**: `@administrador_required`
- **Requisito**: `is_staff = True` en el usuario

## Módulos y Funcionalidades

### Módulo Cliente

#### Portal Cliente (`gestion/templates/cliente/portal_cliente.html`)
- Dashboard personal con resumen de reservas y notificaciones
- Acceso rápido a funciones principales
- URL: `/cliente/`

#### Solicitar Reserva (`gestion/templates/cliente/solicitar_reserva.html`)
- Formulario de reserva con selección de cabaña
- Verificación de disponibilidad en tiempo real
- Cálculo automático del monto según fechas y precio por noche
- URL: `/cliente/solicitar-reserva/`

#### Mis Reservas (`gestion/templates/cliente/mis_reservas.html`)
- Listado completo de reservas del cliente
- Estados visibles con clases CSS
- Acceso a completar encuestas para reservas completadas
- URL: `/cliente/mis-reservas/`

#### Completar Encuesta (`gestion/templates/cliente/completar_encuesta.html`)
- Formulario de satisfacción post-estadía
- Calificación de 1 a 5 estrellas
- Campo de comentarios opcional
- URL: `/cliente/encuesta/<id>/`

#### Solicitar Préstamo (`gestion/templates/cliente/solicitar_prestamo.html`)
- Solicitud de préstamo de implementos
- Requiere reserva activa
- Verificación de disponibilidad de implementos
- URL: `/cliente/solicitar-prestamo/`

### Módulo Administrador

#### Dashboard Administrador (`gestion/templates/admin/dashboard_admin.html`)
- Métricas principales: total reservas, pendientes, próximas, ingresos, ocupación
- Listado de reservas recientes con acciones rápidas
- URL: `/administrador/dashboard/`

#### Gestión de Reservas (`gestion/templates/admin/gestion_reservas.html`)
- Listado completo de reservas con filtros por estado
- Aprobación y cancelación de reservas
- Visualización de detalles completos
- URL: `/administrador/reservas/`

#### Registro de Pagos (`gestion/templates/admin/registro_pagos.html`)
- Registro de pagos con comprobantes
- Historial completo de pagos
- Filtros y búsqueda
- URL: `/administrador/pagos/`

#### Reportes Generales (`gestion/templates/admin/reportes_generales.html`)
- Ocupación por mes
- Ingresos por mes
- Estadísticas de encuestas
- Cabañas más reservadas
- URL: `/administrador/reportes/`

#### Gestión de Clientes (`gestion/templates/admin/gestion_clientes.html`)
- Listado completo de clientes
- Información de contacto y tipo
- Número de reservas por cliente
- URL: `/administrador/clientes/`

#### Visualizar Encuestas (`gestion/templates/admin/visualizar_encuestas.html`)
- Todas las encuestas completadas
- Calificaciones y comentarios
- Filtros por fecha
- URL: `/administrador/encuestas/`

#### Supervisar Mantenimiento (`gestion/templates/admin/supervisar_mantenimiento.html`)
- Vista general de todos los mantenimientos
- Estados y fechas programadas
- URL: `/administrador/mantenimiento/`

### Módulo Encargado

#### Dashboard Encargado (`gestion/templates/encargado/dashboard_encargado.html`)
- Mantenimientos pendientes próximos
- Alertas de faltantes de insumos
- Reservas que requieren preparación
- URL: `/encargado/dashboard/`

#### Inventario de Cabañas (`gestion/templates/encargado/inventario_cabañas.html`)
- Registro de implementos
- Control de stock y disponibilidad
- Alertas automáticas de faltantes
- URL: `/encargado/inventario/`

#### Gestión de Mantenimiento (`gestion/templates/encargado/gestion_mantenimiento.html`)
- Registro de mantenimientos preventivos y correctivos
- Programación de fechas
- Finalización de mantenimientos
- URL: `/encargado/mantenimiento/`

#### Préstamos de Implementos (`gestion/templates/encargado/prestamos_implementos.html`)
- Listado de préstamos activos
- Registro de devoluciones
- Vinculación con reservas
- URL: `/encargado/prestamos/`

#### Estado de Cabañas (`gestion/templates/encargado/estado_cabañas.html`)
- Cambio de estados de cabañas
- Visualización de disponibilidad
- Control de ocupación
- URL: `/encargado/estado-cabañas/`

#### Preparar Cabañas (`gestion/templates/encargado/preparar_cabañas.html`)
- Listado de reservas próximas
- Envío de notificaciones de preparación
- Gestión de preparación previa
- URL: `/encargado/preparar-cabañas/`

## Seguridad

### Implementaciones de Seguridad

1. **Autenticación**: Sistema nativo de Django con hash de contraseñas
2. **Autorización**: Decoradores personalizados por rol
3. **CSRF Protection**: Activado en todos los formularios
4. **Validación de Datos**: Formularios Django con validación
5. **Sanitización**: Django escapa automáticamente contenido HTML
6. **Sesiones**: Manejo seguro de sesiones por usuario

### Restricciones por Rol

- **Clientes**: Solo acceden a sus propios datos
- **Encargados**: No acceden a información financiera
- **Administradores**: Acceso completo con registro de actividades

## Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Virtual environment (recomendado)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**

2. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
# Con un entorno virtual cada proyecto tiene sus propias dependencias
# y no hay conflictos entre proyectos
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear datos iniciales (incluye usuarios de ejemplo)**:
```bash
python manage.py init_data
```

Esto crea automáticamente:
- Usuario **admin** (contraseña: `admin123`) - Administrador
- Usuario **encargado** (contraseña: `encargado123`) - Encargado
- Usuario **cliente** (contraseña: `cliente123`) - Cliente de ejemplo
- Cabañas e implementos de ejemplo
- Grupo "Encargados"

**Nota**: Si quieres crear tu propio superusuario adicional, puedes hacerlo con:
```bash
python manage.py createsuperuser
```

6. **Recopilar archivos estáticos**:
```bash
python manage.py collectstatic
```

7. **Ejecutar servidor de desarrollo**:
```bash
python manage.py runserver
```

8. **Acceder al sistema**:
- URL principal: http://127.0.0.1:8000/
- Admin Django: http://127.0.0.1:8000/admin/
- Dashboard Administrador: http://127.0.0.1:8000/administrador/dashboard/

## Uso del Sistema

### Para Clientes

1. **Registro**: Acceder a `/registro/` y completar el formulario
2. **Login**: Iniciar sesión con usuario y contraseña (o usar usuario de ejemplo: `cliente` / `cliente123`)
3. **Portal Cliente**: Acceder a `/cliente/` para ver dashboard personal
4. **Solicitar Reserva**: Seleccionar cabaña, fechas y número de personas en `/cliente/solicitar-reserva/`
5. **Ver Reservas**: Consultar estado de reservas en `/cliente/mis-reservas/`
6. **Completar Encuesta**: Después de la estadía, completar la encuesta desde "Mis Reservas"
7. **Solicitar Préstamos**: Durante la estadía, solicitar implementos en `/cliente/solicitar-prestamo/`

### Para Administradores

1. **Login**: Iniciar sesión con cuenta de administrador (usuario: `admin`, contraseña: `admin123`)
2. **Dashboard**: Acceder a `/administrador/dashboard/` para ver métricas generales
3. **Aprobar Reservas**: Revisar y aprobar reservas pendientes en `/administrador/reservas/`
4. **Registrar Pagos**: Registrar pagos recibidos con comprobantes en `/administrador/pagos/`
5. **Ver Reportes**: Consultar métricas y estadísticas en `/administrador/reportes/`
6. **Gestionar Clientes**: Ver y administrar base de clientes en `/administrador/clientes/`
7. **Admin Django**: Acceso al panel de administración de Django en `/admin/`

### Para Encargados

1. **Login**: Iniciar sesión con cuenta de encargado (usuario: `encargado`, contraseña: `encargado123`)
2. **Dashboard**: Acceder a `/encargado/dashboard/` para ver tareas pendientes
3. **Gestionar Inventario**: Registrar y controlar implementos en `/encargado/inventario/`
4. **Programar Mantenimientos**: Registrar mantenimientos preventivos en `/encargado/mantenimiento/`
5. **Controlar Préstamos**: Registrar devoluciones de implementos en `/encargado/prestamos/`
6. **Estado de Cabañas**: Cambiar estados de cabañas en `/encargado/estado-cabañas/`
7. **Preparar Cabañas**: Enviar notificaciones de preparación en `/encargado/preparar-cabañas/`

## Funcionalidades Críticas Implementadas

### Sistema de Reservas en Tiempo Real
- Verificación de disponibilidad al momento de solicitar
- Prevención de doble reserva en mismas fechas
- Cálculo automático de montos

### Sistema de Alertas Automáticas
- Alertas a 7 días y 72 horas antes de la reserva
- Notificaciones de preparación
- Alertas de faltantes de inventario

### Gestión de Inventario
- Control de stock en tiempo real
- Alertas automáticas de faltantes (< 20% del total)
- Registro de préstamos y devoluciones

### Módulo de Mantenimiento
- Programación de mantenimientos preventivos y correctivos
- Cambio automático de estado de cabañas
- Seguimiento de mantenimientos

### Sistema de Encuestas
- Encuestas post-estadía
- Calificación de 1 a 5 estrellas
- Comentarios opcionales
- Estadísticas de satisfacción

### Reportes Analytics
- Ocupación por mes
- Ingresos por mes
- Promedio de calificaciones
- Cabañas más reservadas

### Flujo Completo de Pagos
- Registro de pagos con múltiples métodos
- Subida de comprobantes
- Historial completo

## Solución de Problemas

### Problemas Comunes

1. **Error de migraciones**:
   - Ejecutar: `python manage.py makemigrations gestion`
   - Luego: `python manage.py migrate`

2. **Archivos estáticos no cargan**:
   - Ejecutar: `python manage.py collectstatic`
   - Verificar que `gestion/static/css/style.css` existe
   - En desarrollo, Django sirve archivos estáticos automáticamente desde `gestion/static/`

3. **Permisos denegados**:
   - Verificar que el usuario tenga el rol correcto
   - Para encargados: verificar que pertenezcan al grupo "Encargados"

4. **Base de datos vacía**:
   - Ejecutar: `python manage.py init_data` para crear usuarios y datos de ejemplo
   - O crear datos de prueba desde el admin de Django
   - O usar el shell de Django para crear registros

5. **Templates o CSS no se cargan**:
   - Verificar que los templates estén en `gestion/templates/`
   - Verificar que el CSS esté en `gestion/static/css/style.css`
   - Asegurarse de que `APP_DIRS: True` en settings.py

## Mejoras Futuras

- [ ] Calendario interactivo para visualización de ocupación
- [ ] Sistema de notificaciones por email
- [ ] API REST para integraciones externas
- [ ] Dashboard con gráficos interactivos
- [ ] Exportación de reportes a PDF/Excel
- [ ] Sistema de recordatorios automáticos por email
- [ ] App móvil para clientes
- [ ] Integración con pasarelas de pago
- [ ] Sistema de descuentos y promociones
- [ ] Gestión de temporadas y precios dinámicos

## Soporte

Para consultas o problemas, contactar al equipo de desarrollo.

## Licencia

Este proyecto es de uso interno para "Las Cabañitas".

---

**Versión**: 1.0
**Última actualización**: 2024

