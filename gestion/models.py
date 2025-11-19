from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Cliente(models.Model):
    """Modelo para clientes del sistema"""
    idCliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.TextField()
    tipoCliente = models.CharField(max_length=50, default='Regular')
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cliente')

    def solicitarReserva(self):
        """Método para solicitar una reserva"""
        pass

    def confirmarReserva(self):
        """Método para confirmar una reserva"""
        pass

    def completarEncuesta(self):
        """Método para completar encuesta"""
        pass

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Cabaña(models.Model):
    """Modelo para cabañas disponibles"""
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'En Mantenimiento'),
        ('reservada', 'Reservada'),
    ]

    idCabaña = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    capacidad = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    precioNoche = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (Cap: {self.capacidad})"

    class Meta:
        verbose_name = "Cabaña"
        verbose_name_plural = "Cabañas"


class Reserva(models.Model):
    """Modelo para reservas de cabañas"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    idReserva = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    cabaña = models.ForeignKey(Cabaña, on_delete=models.CASCADE, related_name='reservas')
    fechaInicio = models.DateField()
    fechaFin = models.DateField()
    numPersonas = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    montoCotizado = models.DecimalField(max_digits=10, decimal_places=2)
    comentarios = models.TextField(blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def registrarReserva(self):
        """Registra una nueva reserva"""
        pass

    def actualizarReserva(self):
        """Actualiza una reserva existente"""
        pass

    def confirmarReserva(self):
        """Confirma una reserva"""
        self.estado = 'confirmada'
        self.save()

    def generarAlerta(self):
        """Genera alertas para reservas próximas"""
        hoy = timezone.now().date()
        dias_restantes = (self.fechaInicio - hoy).days

        if dias_restantes == 7:
            Notificacion.objects.create(
                usuario=self.cliente.usuario if self.cliente.usuario else None,
                tipo='alerta',
                mensaje=f'Su reserva en {self.cabaña.nombre} es en 7 días',
                fechaEnvio=timezone.now()
            )
        elif dias_restantes == 3:
            Notificacion.objects.create(
                usuario=self.cliente.usuario if self.cliente.usuario else None,
                tipo='alerta',
                mensaje=f'Su reserva en {self.cabaña.nombre} es en 3 días',
                fechaEnvio=timezone.now()
            )

    def enviarNotificacionPreparacion(self):
        """Envía notificación de preparación"""
        Notificacion.objects.create(
            usuario=self.cliente.usuario if self.cliente.usuario else None,
            tipo='preparacion',
            mensaje=f'Su cabaña {self.cabaña.nombre} está siendo preparada',
            fechaEnvio=timezone.now()
        )

    def __str__(self):
        return f"Reserva #{self.idReserva} - {self.cliente.nombre} - {self.cabaña.nombre}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fechaCreacion']


class Encuesta(models.Model):
    """Modelo para encuestas de satisfacción"""
    idEncuesta = models.AutoField(primary_key=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='encuesta')
    calificacion = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comentarios = models.TextField(blank=True)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Encuesta #{self.idEncuesta} - Reserva #{self.reserva.idReserva} - {self.calificacion} estrellas"

    class Meta:
        verbose_name = "Encuesta"
        verbose_name_plural = "Encuestas"


class Pago(models.Model):
    """Modelo para pagos de reservas"""
    METODOS = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('otro', 'Otro'),
    ]

    idPago = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS)
    fechaPago = models.DateField()
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)

    def registrarPago(self):
        """Registra un pago"""
        pass

    def actualizarComprobante(self):
        """Actualiza el comprobante de pago"""
        pass

    def __str__(self):
        return f"Pago #{self.idPago} - {self.reserva} - ${self.monto}"

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"


class Implemento(models.Model):
    """Modelo para implementos/inventario"""
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    idImplemento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidadTotal = models.IntegerField()
    cantidadDisponible = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')

    def actualizarDisponibilidad(self):
        """Actualiza la disponibilidad del implemento"""
        if self.cantidadDisponible <= 0:
            self.estado = 'agotado'
        elif self.cantidadDisponible < (self.cantidadTotal * 0.2):
            # Alerta de bajo stock
            pass
        else:
            self.estado = 'disponible'
        self.save()

    def registrarPrestamo(self, cantidad):
        """Registra un préstamo de implemento"""
        if self.cantidadDisponible >= cantidad:
            self.cantidadDisponible -= cantidad
            self.actualizarDisponibilidad()
            return True
        return False

    def __str__(self):
        return f"{self.nombre} ({self.cantidadDisponible}/{self.cantidadTotal})"

    class Meta:
        verbose_name = "Implemento"
        verbose_name_plural = "Implementos"


class PrestamoImplemento(models.Model):
    """Modelo para préstamos de implementos"""
    idPrestamo = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='prestamos_implementos')
    implemento = models.ForeignKey(Implemento, on_delete=models.CASCADE, related_name='prestamos')
    fechaPrestamo = models.DateField()
    fechaDevolucion = models.DateField(null=True, blank=True)
    cantidad = models.IntegerField()
    devuelto = models.BooleanField(default=False)

    def registrarPrestamo(self):
        """Registra un préstamo"""
        if self.implemento.registrarPrestamo(self.cantidad):
            self.save()
            return True
        return False

    def registrarDevolucion(self):
        """Registra la devolución de un préstamo"""
        if not self.devuelto:
            self.implemento.cantidadDisponible += self.cantidad
            self.implemento.actualizarDisponibilidad()
            self.fechaDevolucion = timezone.now().date()
            self.devuelto = True
            self.save()
            return True
        return False

    def __str__(self):
        return f"Préstamo #{self.idPrestamo} - {self.implemento.nombre} x{self.cantidad}"

    class Meta:
        verbose_name = "Préstamo de Implemento"
        verbose_name_plural = "Préstamos de Implementos"


class Mantenimiento(models.Model):
    """Modelo para mantenimientos de cabañas"""
    TIPOS = [
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
        ('limpieza', 'Limpieza'),
        ('reparacion', 'Reparación'),
    ]

    ESTADOS = [
        ('programado', 'Programado'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    idMantenimiento = models.AutoField(primary_key=True)
    cabaña = models.ForeignKey(Cabaña, on_delete=models.CASCADE, related_name='mantenimientos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField()
    fechaProgramada = models.DateField()
    fechaEjecucion = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programado')

    def registrarMantenimiento(self):
        """Registra un mantenimiento"""
        self.cabaña.estado = 'mantenimiento'
        self.cabaña.save()
        self.save()

    def finalizarMantenimiento(self):
        """Finaliza un mantenimiento"""
        self.estado = 'completado'
        self.fechaEjecucion = timezone.now().date()
        self.cabaña.estado = 'disponible'
        self.cabaña.save()
        self.save()

    def programarMantenimiento(self):
        """Programa un mantenimiento"""
        self.estado = 'programado'
        self.save()

    def __str__(self):
        return f"Mantenimiento #{self.idMantenimiento} - {self.cabaña.nombre} - {self.tipo}"

    class Meta:
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering = ['fechaProgramada']


class Notificacion(models.Model):
    """Modelo para notificaciones del sistema"""
    TIPOS = [
        ('alerta', 'Alerta'),
        ('confirmacion', 'Confirmación'),
        ('preparacion', 'Preparación'),
        ('recordatorio', 'Recordatorio'),
        ('general', 'General'),
    ]

    idNotificacion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    fechaEnvio = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def enviar(self):
        """Envía la notificación"""
        self.save()

    def marcarLeida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.save()

    def __str__(self):
        return f"Notificación #{self.idNotificacion} - {self.tipo} - {self.usuario}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fechaEnvio']

