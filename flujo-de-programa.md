FASE 1: SOLICITUD DE RESERVA (Días/Semanas Antes)
PASO 1.1 - Cliente consulta disponibilidad

```text
USUARIO: Cliente
SISTEMA: Portal Cliente → Calendario Disponibilidad
ACCION: Cliente revisa fechas disponibles en calendario interactivo
```
PASO 1.2 - Cliente solicita reserva

```text
USUARIO: Cliente  
SISTEMA: solicitar_reserva.html
ACCION: Completa formulario (fechas, personas, cabaña preferida)
DATOS: Fechas, número personas, datos contacto, observaciones
```
PASO 1.3 - Sistema valida y crea reserva pendiente

```text
USUARIO: Sistema Automático
SISTEMA: views.solicitar_reserva()
ACCION: Valida disponibilidad, calcula monto, crea Reserva con estado "pendiente"
```
FASE 2: APROBACIÓN ADMINISTRATIVA (1-2 Días Después)
PASO 2.1 - Administrador revisa reservas pendientes

```text
USUARIO: Administrador
SISTEMA: dashboard_admin.html → gestión_reservas.html
ACCION: Ve lista de reservas pendientes, revisa detalles
```
PASO 2.2 - Administrador aprueba/rechaza reserva

```text
USUARIO: Administrador
SISTEMA: gestion_reservas.html
ACCION: Click "Aprobar Reserva" o "Rechazar Reserva"
CAMBIOS: Estado reserva → "confirmada" o "cancelada"
```
PASO 2.3 - Sistema notifica al cliente

```text
USUARIO: Sistema Automático
SISTEMA: models.Reserva.generarAlerta()
ACCION: Envía email/SMS al cliente con confirmación o rechazo
```
FASE 3: CONFIRMACIÓN CLIENTE (4 Días Antes del Check-in)
PASO 3.1 - Sistema envía recordatorio de confirmación

```text
USUARIO: Sistema Automático  
SISTEMA: Tarea programada (4 días antes fecha inicio)
ACCION: Envía recordatorio al cliente para confirmar asistencia
```
PASO 3.2 - Cliente confirma su reserva

```text
USUARIO: Cliente
SISTEMA: portal_cliente.html → mis_reservas.html
ACCION: Click "Confirmar Asistencia" en su reserva
CAMBIOS: Reserva.confirmacion_cliente = True
```
PASO 3.3 - Sistema activa preparación de cabaña

```text
USUARIO: Sistema Automático
SISTEMA: models.Reserva.iniciar_preparacion()
ACCION: Crea tarea automática para encargado, genera checklist
```
FASE 4: PREPARACIÓN CABAÑA (3-1 Días Antes)
PASO 4.1 - Encargado recibe alerta de preparación

```text
USUARIO: Encargado
SISTEMA: dashboard_encargado.html
ACCION: Ve "Reservas Próximas" que requieren preparación
```
PASO 4.2 - Encargado prepara la cabaña

```text
USUARIO: Encargado
SISTEMA: inventario_cabañas.html + gestión_mantenimiento.html
ACCION: 
- Limpieza cabaña
- Revisión inventario
- Mantenimiento preventivo
- Control electrodomésticos
```
PASO 4.3 - Encargado marca cabaña como lista

```text
USUARIO: Encargado
SISTEMA: estado_cabañas.html
ACCION: Cambia estado cabaña → "disponible y preparada"
```
FASE 5: CHECK-IN Y ENTREGA (Día de Llegada)
PASO 5.1 - Cliente llega a recepción

```text
USUARIO: Cliente + Encargado
SISTEMA: checklist_entrega.html (Encargado) + confirmacion_cliente.html (Cliente)
ACCION: Encargado y cliente revisan cabaña juntos
```
PASO 5.2 - Encargado completa checklist digital

```text
USUARIO: Encargado
SISTEMA: checklist_entrega.html
ACCION: 
- Verifica cada ítem del inventario
- Toma fotos de estado inicial
- Registra observaciones
```
PASO 5.3 - Cliente firma digitalmente

```text
USUARIO: Cliente
SISTEMA: confirmacion_cliente.html
ACCION: Revisa checklist, click "Confirmo Recepción"
DATOS: Genera firma digital, timestamp de aceptación
```
PASO 5.4 - Sistema registra entrega completada

```text
USUARIO: Sistema Automático
SISTEMA: models.EntregaCabaña
ACCION: Cambia estado entrega → "entregada", estado reserva → "activa"
```
FASE 6: DURANTE LA ESTADÍA
PASO 6.1 - Cliente solicita préstamo implementos

```text
USUARIO: Cliente
SISTEMA: portal_cliente.html → solicitar_prestamo.html
ACCION: Selecciona implementos recreativos a prestar
```
PASO 6.2 - Encargado gestiona préstamo

```text
USUARIO: Encargado
SISTEMA: prestamos_implementos.html
ACCION: Registra préstamo, actualiza disponibilidad inventario
```
PASO 6.3 - Reporte de incidencias (si aplica)

```text
USUARIO: Cliente o Encargado
SISTEMA: gestion_mantenimiento.html
ACCION: Reporta problemas (ej: electrodoméstico no funciona)
```
FASE 7: CHECK-OUT Y DEVOLUCIÓN (Día de Salida)
PASO 7.1 - Cliente solicita check-out

```text
USUARIO: Cliente
SISTEMA: portal_cliente.html o directamente con encargado
ACCION: Notifica que va a salir, devuelve llaves/implementos
```
PASO 7.2 - Encargado verifica inventario

```text
USUARIO: Encargado
SISTEMA: verificacion_devolucion.html
ACCION: 
- Compara estado actual con checklist inicial
- Identifica faltantes/daños
- Toma fotos de evidencia
```
PASO 7.3 - Sistema calcula cargos automáticos

```text
USUARIO: Sistema Automático
SISTEMA: models.EntregaCabaña.calcular_cargos()
ACCION: Calcula montos por items faltantes/damage
```
PASO 7.4 - Cliente paga cargos (si aplica)

```text
USUARIO: Administrador + Cliente
SISTEMA: registro_pagos.html
ACCION: Administrador registra pago de cargos por faltantes
```
PASO 7.5 - Cliente firma devolución

```text
USUARIO: Cliente
SISTEMA: confirmacion_cliente.html
ACCION: Confirma devolución y acepta cargos (si aplica)
```
FASE 8: CIERRE Y EVALUACIÓN (Después de Salida)
PASO 8.1 - Sistema marca reserva como completada

```text
USUARIO: Sistema Automático
SISTEMA: models.Reserva
ACCION: Cambia estado reserva → "completada"
```
PASO 8.2 - Sistema envía encuesta de satisfacción

```text
USUARIO: Sistema Automático
SISTEMA: Tarea programada (1 día después check-out)
ACCION: Envía email con link a encuesta digital
```
PASO 8.3 - Cliente completa encuesta

```text
USUARIO: Cliente
SISTEMA: completar_encuesta.html
ACCION: Califica experiencia (1-5 estrellas), deja comentarios
```
PASO 8.4 - Administrador revisa feedback

```text
USUARIO: Administrador
SISTEMA: visualizar_encuestas.html + reportes.html
ACCION: Analiza encuestas, genera reportes de satisfacción
