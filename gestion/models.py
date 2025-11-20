from django.db import models
from django.db.models import Q
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
    # Nuevos campos para confirmación del cliente
    confirmacion_cliente = models.BooleanField(default=False, verbose_name='Confirmación Cliente')
    fecha_confirmacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Confirmación')

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
        """Genera alertas para reservas próximas - Actualizado para 4 días exactos"""
        hoy = timezone.now().date()
        dias_restantes = (self.fechaInicio - hoy).days

        # Alerta a 4 días exactos para confirmación
        if dias_restantes == 4 and not self.confirmacion_cliente:
            Notificacion.objects.create(
                usuario=self.cliente.usuario if self.cliente.usuario else None,
                tipo='recordatorio',
                mensaje=f'Por favor confirme su reserva en {self.cabaña.nombre} que inicia en 4 días. Fecha: {self.fechaInicio}',
                fechaEnvio=timezone.now()
            )
        elif dias_restantes == 7:
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

    def confirmar_reserva_cliente(self):
        """Confirma la reserva por parte del cliente"""
        self.confirmacion_cliente = True
        self.fecha_confirmacion = timezone.now()
        self.save()

    @staticmethod
    def verificar_disponibilidad_cabaña(cabaña, fecha_inicio, fecha_fin):
        """Verifica disponibilidad de cabaña considerando mantenimientos"""
        # Verificar si hay mantenimientos activos en el rango de fechas
        mantenimientos = Mantenimiento.objects.filter(
            cabaña=cabaña,
            fechaProgramada__lte=fecha_fin,
            estado__in=['programado', 'en_proceso']
        )

        # Si hay un mantenimiento programado, verificar si hay fecha de ejecución
        for mantenimiento in mantenimientos:
            # Si no tiene fecha de ejecución, asumir que el mantenimiento afecta toda la fecha programada
            if not mantenimiento.fechaEjecucion:
                if mantenimiento.fechaProgramada <= fecha_fin:
                    return False
            # Si tiene fecha de ejecución, verificar si se solapa
            elif mantenimiento.fechaEjecucion >= fecha_inicio:
                return False

        # Verificar si la cabaña está en mantenimiento
        if cabaña.estado == 'mantenimiento':
            return False

        # Verificar reservas existentes
        reservas_existentes = Reserva.objects.filter(
            cabaña=cabaña,
            estado__in=['confirmada', 'pendiente'],
        ).filter(
            Q(fechaInicio__lte=fecha_fin) & Q(fechaFin__gte=fecha_inicio)
        )

        return not reservas_existentes.exists()

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


class ChecklistInventario(models.Model):
    """Modelo para checklist de inventario por cabaña"""
    CATEGORIAS = [
        ('cocina', 'Cocina'),
        ('baño', 'Baño'),
        ('dormitorio', 'Dormitorio'),
        ('sala', 'Sala'),
        ('exterior', 'Exterior'),
        ('otros', 'Otros'),
    ]

    idChecklist = models.AutoField(primary_key=True)
    cabaña = models.ForeignKey(Cabaña, on_delete=models.CASCADE, related_name='checklist_inventario')
    nombre_item = models.CharField(max_length=100, verbose_name='Nombre del Item')
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='otros', verbose_name='Categoría')
    cantidad_esperada = models.IntegerField(default=1, verbose_name='Cantidad Esperada')
    es_obligatorio = models.BooleanField(default=True, verbose_name='Es Obligatorio')
    precio_reposicion = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Precio Reposición')
    orden = models.IntegerField(default=0, verbose_name='Orden')

    # Propiedad para compatibilidad con código que usa .item
    @property
    def item(self):
        return self.nombre_item

    def __str__(self):
        return f"{self.nombre_item} - {self.cabaña.nombre}"

    class Meta:
        verbose_name = "Item de Checklist"
        verbose_name_plural = "Checklist de Inventario"
        ordering = ['cabaña', 'orden', 'categoria', 'nombre_item']


class EntregaCabaña(models.Model):
    """Modelo para registro de entrega de cabaña a cliente"""
    ESTADOS = [
        ('pendiente', 'Pendiente de Entrega'),
        ('entregada', 'Cabaña Entregada'),
        ('devuelta', 'Cabaña Devuelta'),
        ('verificada', 'Inventario Verificado'),
    ]

    idEntrega = models.AutoField(primary_key=True)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='entrega')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Entrega')
    fecha_devolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Devolución')
    encargado_entrega = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='entregas_realizadas', verbose_name='Encargado Entrega')
    cliente_confirma_entrega = models.BooleanField(default=False, verbose_name='Cliente Confirma Entrega')
    cliente_confirma_devolucion = models.BooleanField(default=False, verbose_name='Cliente Confirma Devolución')
    observaciones_entrega = models.TextField(blank=True, verbose_name='Observaciones Entrega')
    observaciones_devolucion = models.TextField(blank=True, verbose_name='Observaciones Devolución')
    firma_digital_entrega = models.CharField(max_length=255, blank=True, verbose_name='Firma Digital Entrega')
    firma_digital_devolucion = models.CharField(max_length=255, blank=True, verbose_name='Firma Digital Devolución')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', verbose_name='Estado')

    # Compatibilidad con campos anteriores
    @property
    def cliente_confirma(self):
        return self.cliente_confirma_entrega

    @property
    def fecha_checkout(self):
        return self.fecha_devolucion

    @property
    def observaciones_checkout(self):
        return self.observaciones_devolucion

    @property
    def firma_digital(self):
        return self.firma_digital_entrega

    def generar_firma_digital(self, tipo='entrega'):
        """Genera un hash único como firma digital"""
        import hashlib
        from django.utils import timezone
        timestamp = timezone.now().timestamp()
        if tipo == 'entrega':
            cadena = f"{self.reserva.idReserva}-{self.reserva.cliente.idCliente}-{timestamp}-entrega"
        else:
            cadena = f"{self.reserva.idReserva}-{self.reserva.cliente.idCliente}-{timestamp}-devolucion"
        return hashlib.sha256(cadena.encode()).hexdigest()

    def __str__(self):
        return f"Entrega #{self.idEntrega} - Reserva #{self.reserva.idReserva} - {self.get_estado_display()}"

    class Meta:
        verbose_name = "Entrega de Cabaña"
        verbose_name_plural = "Entregas de Cabañas"
        ordering = ['-fecha_entrega']


class ItemVerificacion(models.Model):
    """Modelo para registro del estado de cada item en cada entrega"""
    ESTADOS = [
        ('bueno', 'Buen Estado'),
        ('regular', 'Estado Regular'),
        ('danado', 'Dañado'),
        ('faltante', 'Faltante'),
    ]

    idItemVerificacion = models.AutoField(primary_key=True)
    entrega = models.ForeignKey(EntregaCabaña, on_delete=models.CASCADE, related_name='items_verificacion')
    item = models.ForeignKey(ChecklistInventario, on_delete=models.CASCADE, related_name='verificaciones')
    cantidad_entregada = models.IntegerField(default=0, verbose_name='Cantidad Entregada')
    cantidad_devuelta = models.IntegerField(default=0, verbose_name='Cantidad Devuelta')
    estado_entregado = models.CharField(max_length=20, choices=ESTADOS, default='bueno', verbose_name='Estado Entregado')
    estado_devuelto = models.CharField(max_length=20, choices=ESTADOS, default='bueno', verbose_name='Estado Devuelto')
    requiere_reposicion = models.BooleanField(default=False, verbose_name='Requiere Reposición')
    cargo_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Cargo Aplicado')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    def calcular_cargo(self):
        """Calcula el cargo por faltantes o daños"""
        cargo = 0
        if self.cantidad_devuelta < self.cantidad_entregada:
            faltantes = self.cantidad_entregada - self.cantidad_devuelta
            cargo += faltantes * self.item.precio_reposicion

        if self.estado_devuelto == 'danado' and self.cantidad_devuelta > 0:
            cargo += (self.cantidad_devuelta * self.item.precio_reposicion * 0.5)  # 50% del valor por daño

        if self.estado_devuelto == 'regular' and self.cantidad_devuelta > 0:
            cargo += (self.cantidad_devuelta * self.item.precio_reposicion * 0.2)  # 20% del valor por estado regular

        self.cargo_aplicado = cargo
        self.requiere_reposicion = cargo > 0
        self.save()
        return cargo

    def __str__(self):
        return f"Verificación: {self.item.nombre_item} - Entrega #{self.entrega.idEntrega}"

    class Meta:
        verbose_name = "Item de Verificación"
        verbose_name_plural = "Items de Verificación"
        ordering = ['entrega', 'item__orden', 'item__categoria']


class ItemFaltante(models.Model):
    """Modelo legacy para compatibilidad - usar ItemVerificacion en su lugar"""
    idItemFaltante = models.AutoField(primary_key=True)
    entrega = models.ForeignKey(EntregaCabaña, on_delete=models.CASCADE, related_name='items_faltantes')
    item_checklist = models.ForeignKey(ChecklistInventario, on_delete=models.CASCADE, related_name='faltantes')
    cantidad_faltante = models.IntegerField(default=1, verbose_name='Cantidad Faltante')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    def calcular_cargo(self):
        """Calcula el cargo por el item faltante"""
        return self.item_checklist.precio_reposicion * self.cantidad_faltante

    def __str__(self):
        return f"Faltante: {self.item_checklist.nombre_item} - Cantidad: {self.cantidad_faltante}"

    class Meta:
        verbose_name = "Item Faltante"
        verbose_name_plural = "Items Faltantes"
        ordering = ['entrega', 'item_checklist']

