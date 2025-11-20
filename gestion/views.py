from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import timedelta, date
from .models import (
    Cliente, Reserva, Cabaña, Encuesta, Pago,
    Implemento, PrestamoImplemento, Mantenimiento, Notificacion,
    ChecklistInventario, EntregaCabaña, ItemFaltante, ItemVerificacion,
    TareaPreparacion, PreparacionCabaña, ItemPreparacionCompletado
)
from .forms import (
    RegistroClienteForm, ReservaForm, EncuestaForm, PagoForm,
    PrestamoImplementoForm, MantenimientoForm, ImplementoForm
)
from .decorators import cliente_required, administrador_required, encargado_required


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        # Redirigir según rol sin pasar por dashboard para evitar loops
        try:
            if request.user.cliente:
                return redirect('portal_cliente')
        except Cliente.DoesNotExist:
            pass

        if request.user.is_staff:
            return redirect('dashboard_admin')
        elif request.user.groups.filter(name='Encargados').exists():
            return redirect('dashboard_encargado')
        else:
            # Usuario sin rol, hacer logout y mostrar mensaje
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, 'No tiene un rol asignado. Contacte al administrador.')
            return render(request, 'login.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Redirigir directamente según rol
            try:
                if user.cliente:
                    return redirect('portal_cliente')
            except Cliente.DoesNotExist:
                pass

            if user.is_staff:
                return redirect('dashboard_admin')
            elif user.groups.filter(name='Encargados').exists():
                return redirect('dashboard_encargado')
            else:
                messages.error(request, 'No tiene un rol asignado. Contacte al administrador.')
                from django.contrib.auth import logout
                logout(request)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


@login_required
def dashboard(request):
    """Dashboard principal según el rol del usuario"""
    # Verificar si existe el objeto Cliente
    try:
        if request.user.cliente:
            return redirect('portal_cliente')
    except Cliente.DoesNotExist:
        pass

    if request.user.is_staff:
        return redirect('dashboard_admin')
    elif request.user.groups.filter(name='Encargados').exists():
        return redirect('dashboard_encargado')
    else:
        messages.error(request, 'No tiene un rol asignado. Contacte al administrador.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')


def registro_cliente(request):
    """Registro de nuevos clientes"""
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir según rol
        try:
            if request.user.cliente:
                return redirect('portal_cliente')
        except Cliente.DoesNotExist:
            pass
        if request.user.is_staff:
            return redirect('dashboard_admin')
        elif request.user.groups.filter(name='Encargados').exists():
            return redirect('dashboard_encargado')

    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Verificar que el Cliente se creó correctamente
            try:
                cliente = Cliente.objects.get(usuario=user)
                messages.success(request, f'Registro exitoso. Bienvenido {cliente.nombre}. Por favor inicie sesión.')
            except Cliente.DoesNotExist:
                messages.error(request, 'Error al crear el perfil de cliente. Contacte al administrador.')
            return redirect('login')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro_cliente.html', {'form': form})


# ============ MÓDULO CLIENTE ============

@cliente_required
def portal_cliente(request):
    """Dashboard del cliente"""
    cliente = request.user.cliente
    reservas = Reserva.objects.filter(cliente=cliente).order_by('-fechaCreacion')[:5]
    notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fechaEnvio')[:5]

    context = {
        'cliente': cliente,
        'reservas': reservas,
        'notificaciones': notificaciones,
    }
    return render(request, 'cliente/portal_cliente.html', context)


@cliente_required
def solicitar_reserva(request):
    """Solicitar una nueva reserva - Mejorado con verificación de mantenimiento"""
    cliente = request.user.cliente

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = cliente
            reserva.estado = 'pendiente'

            # Calcular monto
            dias = (reserva.fechaFin - reserva.fechaInicio).days
            reserva.montoCotizado = reserva.cabaña.precioNoche * dias

            # Verificar disponibilidad incluyendo mantenimientos
            disponible = Reserva.verificar_disponibilidad_cabaña(
                reserva.cabaña,
                reserva.fechaInicio,
                reserva.fechaFin
            )

            if not disponible:
                # Verificar si es por mantenimiento
                mantenimientos = Mantenimiento.objects.filter(
                    cabaña=reserva.cabaña,
                    fechaProgramada__lte=reserva.fechaFin,
                    estado__in=['programado', 'en_proceso']
                )
                if mantenimientos.exists():
                    messages.error(
                        request,
                        f'La cabaña {reserva.cabaña.nombre} está en mantenimiento en esas fechas. Por favor seleccione otra cabaña o fechas alternativas.'
                    )
                    # Obtener cabañas alternativas disponibles
                    cabañas_alternativas = Cabaña.objects.filter(
                        estado__in=['disponible', 'reservada']
                    ).exclude(idCabaña=reserva.cabaña.idCabaña)

                    if cabañas_alternativas.exists():
                        messages.info(request, 'Hay otras cabañas disponibles. Consulte la lista a continuación.')
                else:
                    messages.error(request, 'La cabaña no está disponible en esas fechas.')
            else:
                reserva.save()
                # Generar alerta inicial
                reserva.generarAlerta()
                messages.success(request, 'Reserva solicitada exitosamente. Esperando confirmación.')
                return redirect('mis_reservas')
    else:
        form = ReservaForm()

    # Solo mostrar cabañas disponibles (no en mantenimiento)
    cabañas = Cabaña.objects.filter(estado__in=['disponible', 'reservada'])

    # Filtrar cabañas con mantenimiento programado
    cabañas_disponibles = []
    for cabaña in cabañas:
        if cabaña.estado != 'mantenimiento':
            cabañas_disponibles.append(cabaña)

    return render(request, 'cliente/solicitar_reserva.html', {
        'form': form,
        'cabañas': cabañas_disponibles
    })


@cliente_required
def mis_reservas(request):
    """Listado de reservas del cliente - Mejorado con confirmaciones pendientes"""
    cliente = request.user.cliente
    hoy = timezone.now().date()

    reservas = Reserva.objects.filter(cliente=cliente).order_by('-fechaCreacion')

    # Enviar recordatorios automáticos a 4 días exactos
    for reserva in reservas:
        dias_restantes = (reserva.fechaInicio - hoy).days
        if dias_restantes == 4 and not reserva.confirmacion_cliente and reserva.estado == 'confirmada':
            reserva.generarAlerta()

    # Separar reservas por confirmar (4 días antes)
    reservas_por_confirmar = []
    reservas_otras = []

    for reserva in reservas:
        dias_restantes = (reserva.fechaInicio - hoy).days
        if dias_restantes <= 4 and dias_restantes >= 0 and not reserva.confirmacion_cliente and reserva.estado == 'confirmada':
            reservas_por_confirmar.append(reserva)
        else:
            reservas_otras.append(reserva)

    return render(request, 'cliente/mis_reservas.html', {
        'reservas': reservas,
        'reservas_por_confirmar': reservas_por_confirmar,
        'reservas_otras': reservas_otras,
        'hoy': hoy
    })


@cliente_required
def completar_encuesta(request, reserva_id):
    """Completar encuesta de satisfacción"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id, cliente=request.user.cliente)

    if Encuesta.objects.filter(reserva=reserva).exists():
        messages.info(request, 'Ya completó la encuesta para esta reserva.')
        return redirect('mis_reservas')

    if request.method == 'POST':
        form = EncuestaForm(request.POST)
        if form.is_valid():
            encuesta = form.save(commit=False)
            encuesta.reserva = reserva
            encuesta.save()
            messages.success(request, 'Encuesta completada. ¡Gracias por su opinión!')
            return redirect('mis_reservas')
    else:
        form = EncuestaForm()

    return render(request, 'cliente/completar_encuesta.html', {'form': form, 'reserva': reserva})


@cliente_required
def solicitar_prestamo(request):
    """Solicitar préstamo de implementos"""
    cliente = request.user.cliente
    reservas_activas = Reserva.objects.filter(
        cliente=cliente,
        estado='confirmada',
        fechaInicio__lte=timezone.now().date(),
        fechaFin__gte=timezone.now().date()
    )

    if request.method == 'POST':
        form = PrestamoImplementoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            if reservas_activas.exists():
                prestamo.reserva = reservas_activas.first()
                if prestamo.registrarPrestamo():
                    messages.success(request, 'Préstamo registrado exitosamente.')
                    return redirect('portal_cliente')
                else:
                    messages.error(request, 'No hay suficientes implementos disponibles.')
            else:
                messages.error(request, 'Debe tener una reserva activa para solicitar préstamos.')
    else:
        form = PrestamoImplementoForm()

    implementos = Implemento.objects.filter(estado='disponible', cantidadDisponible__gt=0)
    return render(request, 'cliente/solicitar_prestamo.html', {
        'form': form,
        'implementos': implementos,
        'reservas_activas': reservas_activas
    })


@cliente_required
def confirmar_reserva_cliente(request, reserva_id):
    """Vista para que el cliente confirme su reserva (4 días antes)"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id, cliente=request.user.cliente)

    hoy = timezone.now().date()
    dias_restantes = (reserva.fechaInicio - hoy).days

    # Solo permitir confirmación si está a 4 días o menos y la reserva está confirmada por admin
    if dias_restantes > 4:
        messages.info(request, 'La confirmación de reserva está disponible 4 días antes de la fecha de inicio.')
        return redirect('mis_reservas')

    if reserva.estado != 'confirmada':
        messages.error(request, 'La reserva debe estar confirmada por el administrador antes de que pueda confirmarla.')
        return redirect('mis_reservas')

    if reserva.confirmacion_cliente:
        messages.info(request, 'Ya ha confirmado esta reserva.')
        return redirect('mis_reservas')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'confirmar':
            reserva.confirmar_reserva_cliente()
            # Iniciar preparación de cabaña automáticamente
            iniciar_preparacion_cabañas(reserva)
            messages.success(request, f'Reserva confirmada exitosamente. La cabaña {reserva.cabaña.nombre} será preparada para su llegada.')
            return redirect('mis_reservas')
        elif accion == 'cancelar':
            # Permitir cancelación con política
            messages.info(request, 'Si desea cancelar su reserva, por favor contacte con el administrador.')
            return redirect('mis_reservas')

    return render(request, 'cliente/confirmar_reserva_cliente.html', {
        'reserva': reserva,
        'dias_restantes': dias_restantes
    })


def generar_checklist_desde_reserva(reserva):
    """Genera checklist automáticamente desde una reserva"""
    # Crear entrega si no existe
    entrega, created = EntregaCabaña.objects.get_or_create(reserva=reserva)

    if created or not entrega.items_verificacion.exists():
        # Copiar items del checklist base de la cabaña
        items_base = ChecklistInventario.objects.filter(cabaña=reserva.cabaña).order_by('orden', 'categoria')

        for item in items_base:
            ItemVerificacion.objects.get_or_create(
                entrega=entrega,
                item=item,
                defaults={
                    'cantidad_entregada': item.cantidad_esperada,
                    'estado_entregado': 'bueno'
                }
            )

    return entrega


def calcular_cargos_devolucion(entrega):
    """Calcula cargos automáticamente por faltantes y daños"""
    total_cargos = 0
    items_verificacion = ItemVerificacion.objects.filter(entrega=entrega)

    for item_ver in items_verificacion:
        cargo = item_ver.calcular_cargo()
        total_cargos += cargo

    return total_cargos


def iniciar_preparacion_cabañas(reserva):
    """Inicia automáticamente la preparación de cabañas para reservas confirmadas"""
    # Crear notificación para el encargado
    usuarios_encargados = User.objects.filter(groups__name='Encargados')
    for usuario in usuarios_encargados:
        Notificacion.objects.create(
            usuario=usuario,
            tipo='preparacion',
            mensaje=f'Preparar cabaña {reserva.cabaña.nombre} para reserva #{reserva.idReserva} - Cliente: {reserva.cliente.nombre} - Fecha inicio: {reserva.fechaInicio}',
            fechaEnvio=timezone.now()
        )

    # Crear entrega y checklist automático si no existe
    if not hasattr(reserva, 'entrega'):
        generar_checklist_desde_reserva(reserva)


@cliente_required
def checklist_entrega(request, reserva_id):
    """Vista para checklist de inventario al entregar cabaña - Cliente"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id, cliente=request.user.cliente)

    # Solo permitir si es la fecha de inicio o después
    hoy = timezone.now().date()
    if reserva.fechaInicio > hoy:
        messages.info(request, 'El checklist de entrega estará disponible el día de inicio de su reserva.')
        return redirect('mis_reservas')

    # Obtener o crear entrega y checklist
    entrega = generar_checklist_desde_reserva(reserva)

    # Obtener items de verificación agrupados por categoría
    items_verificacion = ItemVerificacion.objects.filter(entrega=entrega).order_by('item__orden', 'item__categoria', 'item__nombre_item')

    categorias_items = {}
    for item_ver in items_verificacion:
        categoria = item_ver.item.get_categoria_display()
        if categoria not in categorias_items:
            categorias_items[categoria] = []
        categorias_items[categoria].append(item_ver)

    # Verificar si es checkout (después de fecha fin)
    es_checkout = hoy >= reserva.fechaFin

    if request.method == 'POST':
        tipo_operacion = request.POST.get('tipo', 'entrega')

        if tipo_operacion == 'checkout':
            # Check-out solo puede ser procesado por encargado
            messages.info(request, 'El check-out debe ser verificado por el encargado. Por favor contacte al personal.')
            return redirect('mis_reservas')
        else:
            # Procesar confirmación de entrega por cliente
            if entrega.estado == 'entregada':
                entrega.cliente_confirma_entrega = True
                if not entrega.firma_digital_entrega:
                    entrega.firma_digital_entrega = entrega.generar_firma_digital('entrega')
                entrega.save()

                messages.success(request, 'Checklist de entrega confirmado. ¡Disfrute de su estadía!')
            else:
                messages.info(request, 'El encargado debe completar la verificación de inventario primero.')
            return redirect('mis_reservas')

    return render(request, 'cliente/checklist_entrega.html', {
        'reserva': reserva,
        'entrega': entrega,
        'categorias_items': categorias_items,
        'items_verificacion': items_verificacion,
        'es_checkout': es_checkout,
        'hoy': hoy
    })


def enviar_recordatorio_confirmacion():
    """Función para enviar recordatorios automáticos a 4 días exactos"""
    hoy = timezone.now().date()
    fecha_objetivo = hoy + timedelta(days=4)

    reservas_pendientes = Reserva.objects.filter(
        fechaInicio=fecha_objetivo,
        confirmacion_cliente=False,
        estado='confirmada'
    )

    for reserva in reservas_pendientes:
        reserva.generarAlerta()

        # Crear notificación adicional
        if reserva.cliente.usuario:
            Notificacion.objects.create(
                usuario=reserva.cliente.usuario,
                tipo='recordatorio',
                mensaje=f'URGENTE: Confirme su reserva en {reserva.cabaña.nombre} que inicia en 4 días ({reserva.fechaInicio}). Acceda a "Mis Reservas" para confirmar.',
                fechaEnvio=timezone.now()
            )


# ============ MÓDULO ADMINISTRADOR ============

@administrador_required
def dashboard_admin(request):
    """Dashboard del administrador"""
    hoy = timezone.now().date()

    # Métricas
    total_reservas = Reserva.objects.count()
    reservas_pendientes = Reserva.objects.filter(estado='pendiente').count()
    reservas_proximas = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=7),
        fechaInicio__gte=hoy,
        estado='confirmada'
    ).count()

    ingresos_mes = Pago.objects.filter(
        fechaPago__year=hoy.year,
        fechaPago__month=hoy.month
    ).aggregate(total=Sum('monto'))['total'] or 0

    ocupacion_actual = Reserva.objects.filter(
        fechaInicio__lte=hoy,
        fechaFin__gte=hoy,
        estado='confirmada'
    ).count()

    total_cabañas = Cabaña.objects.count()
    tasa_ocupacion = (ocupacion_actual / total_cabañas * 100) if total_cabañas > 0 else 0

    # Reservas recientes
    reservas_recientes = Reserva.objects.order_by('-fechaCreacion')[:10]

    context = {
        'total_reservas': total_reservas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_proximas': reservas_proximas,
        'ingresos_mes': ingresos_mes,
        'tasa_ocupacion': tasa_ocupacion,
        'reservas_recientes': reservas_recientes,
    }
    return render(request, 'admin/dashboard_admin.html', context)


@administrador_required
def gestion_reservas(request):
    """Gestión de reservas por administrador"""
    estado_filtro = request.GET.get('estado', '')

    reservas = Reserva.objects.all().order_by('-fechaCreacion')
    if estado_filtro:
        reservas = reservas.filter(estado=estado_filtro)

    return render(request, 'admin/gestion_reservas.html', {
        'reservas': reservas,
        'estado_filtro': estado_filtro
    })


@administrador_required
def aprobar_reserva(request, reserva_id):
    """Aprobar una reserva"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id)
    reserva.confirmarReserva()
    reserva.generarAlerta()
    messages.success(request, f'Reserva #{reserva.idReserva} confirmada exitosamente.')
    return redirect('gestion_reservas')


@administrador_required
def cancelar_reserva(request, reserva_id):
    """Cancelar una reserva"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id)
    reserva.estado = 'cancelada'
    reserva.save()
    messages.success(request, f'Reserva #{reserva.idReserva} cancelada.')
    return redirect('gestion_reservas')


@administrador_required
def registro_pagos(request):
    """Registro y seguimiento de pagos"""
    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pago registrado exitosamente.')
            return redirect('registro_pagos')
    else:
        form = PagoForm()

    pagos = Pago.objects.all().order_by('-fechaPago')
    return render(request, 'admin/registro_pagos.html', {'form': form, 'pagos': pagos})


@administrador_required
def reportes_generales(request):
    """Reportes generales del sistema"""
    hoy = timezone.now().date()

    # Reporte de ocupación
    ocupacion_mes = {}
    for mes in range(1, 13):
        reservas_mes = Reserva.objects.filter(
            fechaInicio__year=hoy.year,
            fechaInicio__month=mes,
            estado='confirmada'
        ).count()
        ocupacion_mes[mes] = reservas_mes

    # Ingresos por mes
    ingresos_mes = {}
    for mes in range(1, 13):
        ingresos = Pago.objects.filter(
            fechaPago__year=hoy.year,
            fechaPago__month=mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        ingresos_mes[mes] = ingresos

    # Encuestas
    encuestas = Encuesta.objects.all()
    total_encuestas = encuestas.count()
    if total_encuestas > 0:
        suma_calificaciones = sum(e.calificacion for e in encuestas)
        promedio_calificacion = suma_calificaciones / total_encuestas
    else:
        promedio_calificacion = 0

    # Cabañas más reservadas
    cabañas_populares = Cabaña.objects.annotate(
        num_reservas=Count('reservas')
    ).order_by('-num_reservas')[:5]

    context = {
        'ocupacion_mes': ocupacion_mes,
        'ingresos_mes': ingresos_mes,
        'promedio_calificacion': round(promedio_calificacion, 2),
        'cabañas_populares': cabañas_populares,
        'total_encuestas': encuestas.count(),
    }
    return render(request, 'admin/reportes_generales.html', context)


@administrador_required
def gestion_clientes(request):
    """Gestión de clientes"""
    clientes = Cliente.objects.all().order_by('nombre')
    return render(request, 'admin/gestion_clientes.html', {'clientes': clientes})


@administrador_required
def visualizar_encuestas(request):
    """Visualizar encuestas de clientes"""
    encuestas = Encuesta.objects.all().order_by('-fecha')
    return render(request, 'admin/visualizar_encuestas.html', {'encuestas': encuestas})


@administrador_required
def supervisar_mantenimiento(request):
    """Supervisar mantenimientos"""
    mantenimientos = Mantenimiento.objects.all().order_by('-fechaProgramada')
    return render(request, 'admin/supervisar_mantenimiento.html', {'mantenimientos': mantenimientos})


# ============ MÓDULO ENCARGADO ============

@encargado_required
def dashboard_encargado(request):
    """Dashboard del encargado - Expandido con confirmaciones pendientes"""
    hoy = timezone.now().date()

    # Tareas pendientes
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado__in=['programado', 'en_proceso'],
        fechaProgramada__lte=hoy + timedelta(days=7)
    ).order_by('fechaProgramada')[:5]

    # Alertas de faltantes
    implementos_faltantes = Implemento.objects.filter(
        Q(cantidadDisponible=0) | Q(cantidadDisponible__lt=F('cantidadTotal') * 0.2)
    )

    # Cabañas que necesitan preparación (solo confirmadas por cliente)
    reservas_proximas = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=3),
        fechaInicio__gte=hoy,
        estado='confirmada',
        confirmacion_cliente=True
    ).select_related('cliente', 'cabaña', 'entrega').order_by('fechaInicio')

    # Confirmaciones pendientes (reservas confirmadas por admin pero no por cliente)
    confirmaciones_pendientes = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=4),
        fechaInicio__gte=hoy,
        estado='confirmada',
        confirmacion_cliente=False
    ).order_by('fechaInicio')

    # Cabañas que requieren preparación urgente
    reservas_urgentes = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=1),
        fechaInicio__gte=hoy,
        estado='confirmada',
        confirmacion_cliente=True
    ).select_related('cliente', 'cabaña', 'entrega')

    context = {
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'implementos_faltantes': implementos_faltantes,
        'reservas_proximas': reservas_proximas,
        'confirmaciones_pendientes': confirmaciones_pendientes,
        'reservas_urgentes': reservas_urgentes,
        'hoy': hoy,
    }
    return render(request, 'encargado/dashboard_encargado.html', context)


@encargado_required
def inventario_cabañas(request):
    """Registro y control de inventario"""
    if request.method == 'POST':
        form = ImplementoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Implemento registrado exitosamente.')
            return redirect('inventario_cabañas')
    else:
        form = ImplementoForm()

    implementos = Implemento.objects.all().order_by('nombre')
    return render(request, 'encargado/inventario_cabañas.html', {'form': form, 'implementos': implementos})


@encargado_required
def gestion_mantenimiento(request):
    """Programación y seguimiento de mantenimientos"""
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mantenimiento = form.save(commit=False)
            mantenimiento.registrarMantenimiento()
            messages.success(request, 'Mantenimiento registrado exitosamente.')
            return redirect('gestion_mantenimiento')
    else:
        form = MantenimientoForm()

    mantenimientos = Mantenimiento.objects.all().order_by('-fechaProgramada')
    return render(request, 'encargado/gestion_mantenimiento.html', {
        'form': form,
        'mantenimientos': mantenimientos
    })


@encargado_required
def finalizar_mantenimiento(request, mantenimiento_id):
    """Finalizar un mantenimiento"""
    mantenimiento = get_object_or_404(Mantenimiento, idMantenimiento=mantenimiento_id)
    mantenimiento.finalizarMantenimiento()
    messages.success(request, f'Mantenimiento #{mantenimiento.idMantenimiento} finalizado.')
    return redirect('gestion_mantenimiento')


@encargado_required
def prestamos_implementos(request):
    """Gestión de préstamos y devoluciones"""
    prestamos = PrestamoImplemento.objects.filter(devuelto=False).order_by('fechaPrestamo')
    return render(request, 'encargado/prestamos_implementos.html', {'prestamos': prestamos})


@encargado_required
def registrar_devolucion(request, prestamo_id):
    """Registrar devolución de implemento"""
    prestamo = get_object_or_404(PrestamoImplemento, idPrestamo=prestamo_id)
    if prestamo.registrarDevolucion():
        messages.success(request, 'Devolución registrada exitosamente.')
    else:
        messages.error(request, 'Error al registrar la devolución.')
    return redirect('prestamos_implementos')


@encargado_required
def estado_cabañas(request):
    """Control de estados de cabañas"""
    cabañas = Cabaña.objects.all().order_by('nombre')

    if request.method == 'POST':
        cabaña_id = request.POST.get('cabaña_id')
        nuevo_estado = request.POST.get('estado')
        cabaña = get_object_or_404(Cabaña, idCabaña=cabaña_id)
        cabaña.estado = nuevo_estado
        cabaña.save()
        messages.success(request, f'Estado de {cabaña.nombre} actualizado.')
        return redirect('estado_cabañas')

    return render(request, 'encargado/estado_cabañas.html', {'cabañas': cabañas})


@encargado_required
def preparar_cabañas(request):
    """Lista de cabañas que requieren preparación"""
    hoy = timezone.now().date()
    reservas_proximas = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=3),
        fechaInicio__gte=hoy,
        estado='confirmada',
        confirmacion_cliente=True
    ).select_related('cliente', 'cabaña', 'entrega').order_by('fechaInicio')

    # Preparaciones existentes
    preparaciones = PreparacionCabaña.objects.filter(
        reserva__in=reservas_proximas
    ).select_related('reserva', 'encargado')

    preparaciones_dict = {p.reserva.idReserva: p for p in preparaciones}

    return render(request, 'encargado/preparar_cabañas.html', {
        'reservas_proximas': reservas_proximas,
        'preparaciones': preparaciones_dict,
        'hoy': hoy
    })


@encargado_required
def preparacion_cabaña(request, reserva_id):
    """Vista detallada de preparación de cabaña"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id)

    # Crear o obtener preparación
    preparacion, created = PreparacionCabaña.objects.get_or_create(
        reserva=reserva,
        defaults={
            'encargado': request.user,
            'estado': 'en_proceso'
        }
    )

    if created:
        # Inicializar tareas de preparación
        tareas = TareaPreparacion.objects.all().order_by('categoria', 'orden')
        for tarea in tareas:
            ItemPreparacionCompletado.objects.create(
                preparacion=preparacion,
                tarea=tarea,
                completado=False
            )

    # Obtener items de preparación agrupados por categoría
    items_preparacion = ItemPreparacionCompletado.objects.filter(
        preparacion=preparacion
    ).select_related('tarea').order_by('tarea__categoria', 'tarea__orden')

    tareas_por_categoria = {}
    for item in items_preparacion:
        categoria_display = item.tarea.get_categoria_display()
        if categoria_display not in tareas_por_categoria:
            tareas_por_categoria[categoria_display] = []
        tareas_por_categoria[categoria_display].append(item)

    porcentaje_completado = preparacion.porcentaje_completado()
    dias_restantes = (reserva.fechaInicio - timezone.now().date()).days

    if request.method == 'POST':
        # Procesar tareas completadas
        tareas_completadas = request.POST.getlist('tareas_completadas')

        # Actualizar estado de tareas
        for item in items_preparacion:
            tarea_id = str(item.tarea.idTareaPreparacion)
            if tarea_id in tareas_completadas:
                if not item.completado:
                    item.completado = True
                    item.fecha_completado = timezone.now()
                    item.save()
            else:
                if item.completado:
                    item.completado = False
                    item.fecha_completado = None
                    item.save()

        # Actualizar observaciones
        observaciones = request.POST.get('observaciones', '')
        preparacion.observaciones = observaciones

        # Verificar si todas las tareas están completadas
        porcentaje = preparacion.porcentaje_completado()
        if request.POST.get('completar_preparacion'):
            preparacion.estado = 'completada'
            preparacion.fecha_completacion = timezone.now()
            messages.success(request, 'Preparación completada exitosamente. La cabaña está lista para entrega.')
        elif porcentaje > 0:
            preparacion.estado = 'en_proceso'
        else:
            preparacion.estado = 'pendiente'

        preparacion.save()

        # Redirigir según acción
        if request.POST.get('completar_preparacion'):
            # Crear entrega automáticamente si no existe
            generar_checklist_desde_reserva(reserva)
            messages.success(request, 'Preparación completada. El checklist de entrega está listo.')
            return redirect('checklist_entrega_encargado', reserva_id=reserva.idReserva)

        return redirect('preparacion_cabaña', reserva_id=reserva.idReserva)

    return render(request, 'encargado/preparacion_cabaña.html', {
        'reserva': reserva,
        'preparacion': preparacion,
        'tareas_por_categoria': tareas_por_categoria,
        'items_preparacion': items_preparacion,
        'porcentaje_completado': porcentaje_completado,
        'dias_restantes': dias_restantes
    })


@encargado_required
def checklist_entrega_encargado(request, reserva_id):
    """Checklist de entrega para encargados - Check-in"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id)

    # Verificar que existe checklist base para esta cabaña
    items_checklist_base = ChecklistInventario.objects.filter(cabaña=reserva.cabaña)

    if not items_checklist_base.exists():
        messages.warning(
            request,
            f'⚠️ No hay items configurados en el checklist para {reserva.cabaña.nombre}. '
            f'Por favor ejecuta: python manage.py poblar_checklist'
        )
        return redirect('dashboard_encargado')

    # Generar checklist automáticamente si no existe
    entrega = generar_checklist_desde_reserva(reserva)

    # Obtener items de verificación agrupados por categoría
    items_verificacion = ItemVerificacion.objects.filter(entrega=entrega).order_by('item__orden', 'item__categoria', 'item__nombre_item')

    if not items_verificacion.exists():
        # Si no hay items de verificación, crearlos desde el checklist base
        for item_checklist in items_checklist_base:
            ItemVerificacion.objects.get_or_create(
                entrega=entrega,
                item=item_checklist,
                defaults={
                    'cantidad_entregada': item_checklist.cantidad_esperada,
                    'estado_entregado': 'bueno'
                }
            )
        items_verificacion = ItemVerificacion.objects.filter(entrega=entrega).order_by('item__orden', 'item__categoria', 'item__nombre_item')

    categorias_items = {}
    for item_ver in items_verificacion:
        categoria = item_ver.item.get_categoria_display()
        if categoria not in categorias_items:
            categorias_items[categoria] = []
        categorias_items[categoria].append(item_ver)

    if request.method == 'POST':
        # Procesar verificación del encargado
        entrega.fecha_entrega = timezone.now()
        entrega.encargado_entrega = request.user
        entrega.estado = 'entregada'
        entrega.observaciones_entrega = request.POST.get('observaciones_entrega', '')

        # Actualizar items de verificación
        for item_ver in items_verificacion:
            cantidad_entregada = request.POST.get(f'cantidad_{item_ver.idItemVerificacion}', item_ver.item.cantidad_esperada)
            estado_entregado = request.POST.get(f'estado_{item_ver.idItemVerificacion}', 'bueno')
            observaciones_item = request.POST.get(f'obs_{item_ver.idItemVerificacion}', '')

            item_ver.cantidad_entregada = int(cantidad_entregada)
            item_ver.estado_entregado = estado_entregado
            if observaciones_item:
                item_ver.observaciones = observaciones_item
            item_ver.save()

        entrega.save()

        messages.success(request, f'Checklist de entrega completado para {reserva.cabaña.nombre}. El cliente puede confirmar la recepción.')
        return redirect('dashboard_encargado')

    return render(request, 'encargado/checklist_entrega.html', {
        'reserva': reserva,
        'entrega': entrega,
        'categorias_items': categorias_items,
        'items_verificacion': items_verificacion
    })


@encargado_required
def verificacion_devolucion(request, reserva_id):
    """Verificación de devolución para encargados - Check-out"""
    reserva = get_object_or_404(Reserva, idReserva=reserva_id)
    entrega = get_object_or_404(EntregaCabaña, reserva=reserva)

    # Obtener items de verificación
    items_verificacion = ItemVerificacion.objects.filter(entrega=entrega).order_by('item__orden', 'item__categoria', 'item__nombre_item')

    categorias_items = {}
    for item_ver in items_verificacion:
        categoria = item_ver.item.get_categoria_display()
        if categoria not in categorias_items:
            categorias_items[categoria] = []
        categorias_items[categoria].append(item_ver)

    if request.method == 'POST':
        # Procesar verificación de devolución
        entrega.fecha_devolucion = timezone.now()
        entrega.estado = 'verificada'
        entrega.observaciones_devolucion = request.POST.get('observaciones_devolucion', '')

        # Actualizar items de verificación
        for item_ver in items_verificacion:
            cantidad_devuelta = request.POST.get(f'cantidad_{item_ver.idItemVerificacion}', 0)
            estado_devuelto = request.POST.get(f'estado_{item_ver.idItemVerificacion}', 'bueno')
            observaciones_item = request.POST.get(f'obs_{item_ver.idItemVerificacion}', '')

            item_ver.cantidad_devuelta = int(cantidad_devuelta)
            item_ver.estado_devuelto = estado_devuelto
            if observaciones_item:
                item_ver.observaciones += f"\n[Check-out] {observaciones_item}"
            item_ver.save()

        entrega.save()

        # Calcular cargos automáticamente
        total_cargos = calcular_cargos_devolucion(entrega)

        messages.success(request, f'Verificación de devolución completada. Cargos totales: ${total_cargos:.2f}')
        return redirect('historial_entregas')

    # Calcular cargos previos
    total_cargos = sum(item.cargo_aplicado for item in items_verificacion)

    return render(request, 'encargado/verificacion_devolucion.html', {
        'reserva': reserva,
        'entrega': entrega,
        'categorias_items': categorias_items,
        'items_verificacion': items_verificacion,
        'total_cargos': total_cargos
    })


@administrador_required
def historial_entregas(request):
    """Historial de entregas para administradores"""
    entregas = EntregaCabaña.objects.all().order_by('-fecha_entrega')

    # Métricas
    total_entregas = entregas.count()
    entregas_completadas = entregas.filter(estado='verificada').count()

    # Calcular total de cargos de forma eficiente
    total_cargos = ItemVerificacion.objects.filter(
        entrega__estado='verificada'
    ).aggregate(total=Sum('cargo_aplicado'))['total'] or 0

    # Items más frecuentemente dañados
    items_danados = ItemVerificacion.objects.filter(
        estado_devuelto__in=['danado', 'faltante'],
        requiere_reposicion=True
    ).values('item__nombre_item').annotate(
        veces_danado=Count('idItemVerificacion'),
        cargo_total=Sum('cargo_aplicado')
    ).order_by('-veces_danado')[:10]

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        entregas = entregas.filter(estado=estado_filtro)

    # Calcular cargos por entrega para el template
    entregas_con_cargos = []
    for entrega in entregas:
        cargo_entrega = sum(
            float(item.cargo_aplicado or 0)
            for item in entrega.items_verificacion.all()
        )
        entregas_con_cargos.append((entrega, cargo_entrega))

    return render(request, 'admin/historial_entregas.html', {
        'entregas_con_cargos': entregas_con_cargos,
        'total_entregas': total_entregas,
        'entregas_completadas': entregas_completadas,
        'total_cargos': total_cargos,
        'items_danados': items_danados,
        'estado_filtro': estado_filtro
    })


@administrador_required
def gestion_incidentes(request):
    """Gestión de incidentes y cabañas no disponibles"""
    cabañas_mantenimiento = Cabaña.objects.filter(estado='mantenimiento')
    mantenimientos_activos = Mantenimiento.objects.filter(
        estado__in=['programado', 'en_proceso']
    ).order_by('-fechaProgramada')

    # Reservas afectadas por mantenimientos
    hoy = timezone.now().date()
    reservas_afectadas = []
    for mantenimiento in mantenimientos_activos:
        reservas = Reserva.objects.filter(
            cabaña=mantenimiento.cabaña,
            estado__in=['confirmada', 'pendiente'],
            fechaInicio__gte=hoy,
            fechaFin__gte=mantenimiento.fechaProgramada
        )
        reservas_afectadas.extend([(mantenimiento, r) for r in reservas])

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'reasignar':
            # Reasignar reserva a otra cabaña
            reserva_id = request.POST.get('reserva_id')
            nueva_cabaña_id = request.POST.get('nueva_cabaña')

            reserva = get_object_or_404(Reserva, idReserva=reserva_id)
            nueva_cabaña = get_object_or_404(Cabaña, idCabaña=nueva_cabaña_id)

            # Verificar disponibilidad de nueva cabaña
            if Reserva.verificar_disponibilidad_cabaña(nueva_cabaña, reserva.fechaInicio, reserva.fechaFin):
                reserva.cabaña = nueva_cabaña
                reserva.save()

                # Notificar al cliente
                if reserva.cliente.usuario:
                    Notificacion.objects.create(
                        usuario=reserva.cliente.usuario,
                        tipo='general',
                        mensaje=f'Su reserva #{reserva.idReserva} ha sido reasignada a {nueva_cabaña.nombre} debido a mantenimiento en la cabaña original.',
                        fechaEnvio=timezone.now()
                    )

                messages.success(request, f'Reserva #{reserva.idReserva} reasignada exitosamente a {nueva_cabaña.nombre}.')
            else:
                messages.error(request, f'La cabaña {nueva_cabaña.nombre} no está disponible en esas fechas.')

        elif accion == 'reprogramar':
            # Reprogramar reserva
            reserva_id = request.POST.get('reserva_id')
            nueva_fecha_inicio = request.POST.get('nueva_fecha_inicio')
            nueva_fecha_fin = request.POST.get('nueva_fecha_fin')

            reserva = get_object_or_404(Reserva, idReserva=reserva_id)

            from datetime import datetime
            nueva_inicio = datetime.strptime(nueva_fecha_inicio, '%Y-%m-%d').date()
            nueva_fin = datetime.strptime(nueva_fecha_fin, '%Y-%m-%d').date()

            # Verificar disponibilidad en nuevas fechas
            if Reserva.verificar_disponibilidad_cabaña(reserva.cabaña, nueva_inicio, nueva_fin):
                reserva.fechaInicio = nueva_inicio
                reserva.fechaFin = nueva_fin
                # Recalcular monto
                dias = (nueva_fin - nueva_inicio).days
                reserva.montoCotizado = reserva.cabaña.precioNoche * dias
                reserva.save()

                # Notificar al cliente
                if reserva.cliente.usuario:
                    Notificacion.objects.create(
                        usuario=reserva.cliente.usuario,
                        tipo='general',
                        mensaje=f'Su reserva #{reserva.idReserva} ha sido reprogramada para {nueva_inicio} - {nueva_fin} debido a mantenimiento.',
                        fechaEnvio=timezone.now()
                    )

                messages.success(request, f'Reserva #{reserva.idReserva} reprogramada exitosamente.')
            else:
                messages.error(request, 'Las nuevas fechas no están disponibles para esta cabaña.')

        elif accion == 'cancelar':
            # Cancelar reserva afectada
            reserva_id = request.POST.get('reserva_id')
            reserva = get_object_or_404(Reserva, idReserva=reserva_id)
            reserva.estado = 'cancelada'
            reserva.save()

            # Notificar al cliente
            if reserva.cliente.usuario:
                Notificacion.objects.create(
                    usuario=reserva.cliente.usuario,
                    tipo='general',
                    mensaje=f'Su reserva #{reserva.idReserva} ha sido cancelada debido a mantenimiento. Contacte al administrador para más información.',
                    fechaEnvio=timezone.now()
                )

            messages.success(request, f'Reserva #{reserva.idReserva} cancelada exitosamente.')

        return redirect('gestion_incidentes')

    # Obtener cabañas disponibles para reasignación
    cabañas_disponibles = Cabaña.objects.filter(estado__in=['disponible', 'reservada'])

    return render(request, 'admin/gestion_incidentes.html', {
        'cabañas_mantenimiento': cabañas_mantenimiento,
        'mantenimientos_activos': mantenimientos_activos,
        'reservas_afectadas': reservas_afectadas,
        'cabañas_disponibles': cabañas_disponibles
    })

