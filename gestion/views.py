from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import timedelta, date
from .models import (
    Cliente, Reserva, Cabaña, Encuesta, Pago,
    Implemento, PrestamoImplemento, Mantenimiento, Notificacion
)
from .forms import (
    RegistroClienteForm, ReservaForm, EncuestaForm, PagoForm,
    PrestamoImplementoForm, MantenimientoForm, ImplementoForm
)
from .decorators import cliente_required, administrador_required, encargado_required


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')


@login_required
def dashboard(request):
    """Dashboard principal según el rol del usuario"""
    if hasattr(request.user, 'cliente'):
        return redirect('portal_cliente')
    elif request.user.is_staff:
        return redirect('dashboard_admin')
    elif request.user.groups.filter(name='Encargados').exists():
        return redirect('dashboard_encargado')
    else:
        messages.info(request, 'No tiene un rol asignado. Contacte al administrador.')
        return redirect('login')


def registro_cliente(request):
    """Registro de nuevos clientes"""
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro exitoso. Por favor inicie sesión.')
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
    """Solicitar una nueva reserva"""
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

            # Verificar disponibilidad
            reservas_existentes = Reserva.objects.filter(
                cabaña=reserva.cabaña,
                estado__in=['confirmada', 'pendiente'],
            ).filter(
                Q(fechaInicio__lte=reserva.fechaFin) & Q(fechaFin__gte=reserva.fechaInicio)
            )

            if reservas_existentes.exists():
                messages.error(request, 'La cabaña no está disponible en esas fechas.')
            else:
                reserva.save()
                messages.success(request, 'Reserva solicitada exitosamente. Esperando confirmación.')
                return redirect('mis_reservas')
    else:
        form = ReservaForm()

    cabañas = Cabaña.objects.filter(estado__in=['disponible', 'reservada'])
    return render(request, 'cliente/solicitar_reserva.html', {'form': form, 'cabañas': cabañas})


@cliente_required
def mis_reservas(request):
    """Listado de reservas del cliente"""
    cliente = request.user.cliente
    reservas = Reserva.objects.filter(cliente=cliente).order_by('-fechaCreacion')
    return render(request, 'cliente/mis_reservas.html', {'reservas': reservas})


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
    """Dashboard del encargado"""
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

    # Cabañas que necesitan preparación
    reservas_proximas = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=1),
        fechaInicio__gte=hoy,
        estado='confirmada'
    )

    context = {
        'mantenimientos_pendientes': mantenimientos_pendientes,
        'implementos_faltantes': implementos_faltantes,
        'reservas_proximas': reservas_proximas,
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
    """Preparar cabañas para reservas próximas"""
    hoy = timezone.now().date()
    reservas_proximas = Reserva.objects.filter(
        fechaInicio__lte=hoy + timedelta(days=1),
        fechaInicio__gte=hoy,
        estado='confirmada'
    )

    if request.method == 'POST':
        reserva_id = request.POST.get('reserva_id')
        reserva = get_object_or_404(Reserva, idReserva=reserva_id)
        reserva.enviarNotificacionPreparacion()
        messages.success(request, f'Notificación de preparación enviada para {reserva.cabaña.nombre}.')
        return redirect('preparar_cabañas')

    return render(request, 'encargado/preparar_cabañas.html', {'reservas_proximas': reservas_proximas})

