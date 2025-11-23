from django.contrib import admin
from .models import (
    Cliente, Reserva, Cabaña, Pago,
    Implemento, PrestamoImplemento,
    Notificacion, ChecklistInventario, EntregaCabaña, ItemVerificacion,
    TareaPreparacion, PreparacionCabaña, ItemPreparacionCompletado, ReporteFaltantes
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('idCliente', 'nombre', 'telefono', 'email', 'tipoCliente')
    search_fields = ('nombre', 'email', 'telefono')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('idReserva', 'cliente', 'cabaña', 'fechaInicio', 'fechaFin', 'estado', 'confirmacion_cliente', 'montoCotizado')
    list_filter = ('estado', 'confirmacion_cliente', 'fechaInicio')
    search_fields = ('cliente__nombre', 'cabaña__nombre')
    readonly_fields = ('fechaCreacion', 'fecha_confirmacion')

@admin.register(Cabaña)
class CabañaAdmin(admin.ModelAdmin):
    list_display = ('idCabaña', 'nombre', 'capacidad', 'estado', 'precioNoche')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('idPago', 'reserva', 'monto', 'metodo', 'fechaPago')
    list_filter = ('metodo', 'fechaPago')

@admin.register(Implemento)
class ImplementoAdmin(admin.ModelAdmin):
    list_display = ('idImplemento', 'nombre', 'cantidadTotal', 'cantidadDisponible', 'estado')

@admin.register(PrestamoImplemento)
class PrestamoImplementoAdmin(admin.ModelAdmin):
    list_display = ('idPrestamo', 'reserva', 'implemento', 'fechaPrestamo', 'fechaDevolucion', 'cantidad')

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('idNotificacion', 'usuario', 'tipo', 'fechaEnvio', 'leida')
    list_filter = ('tipo', 'leida')

@admin.register(ChecklistInventario)
class ChecklistInventarioAdmin(admin.ModelAdmin):
    list_display = ('idChecklist', 'cabaña', 'nombre_item', 'categoria', 'cantidad_esperada', 'precio_reposicion', 'es_obligatorio', 'orden')
    list_filter = ('cabaña', 'categoria', 'es_obligatorio')
    search_fields = ('nombre_item', 'cabaña__nombre')
    ordering = ('cabaña', 'orden', 'categoria', 'nombre_item')

@admin.register(EntregaCabaña)
class EntregaCabañaAdmin(admin.ModelAdmin):
    list_display = ('idEntrega', 'reserva', 'fecha_entrega', 'cliente_confirma_entrega', 'fecha_devolucion', 'estado', 'encargado_entrega')
    list_filter = ('estado', 'cliente_confirma_entrega', 'fecha_entrega')
    search_fields = ('reserva__cliente__nombre', 'reserva__cabaña__nombre')
    readonly_fields = ('firma_digital_entrega', 'firma_digital_devolucion')

@admin.register(ItemVerificacion)
class ItemVerificacionAdmin(admin.ModelAdmin):
    list_display = ('idItemVerificacion', 'entrega', 'item', 'cantidad_entregada', 'cantidad_devuelta', 'estado_entregado', 'estado_devuelto', 'cargo_aplicado')
    list_filter = ('estado_entregado', 'estado_devuelto', 'requiere_reposicion', 'entrega')
    search_fields = ('item__nombre_item', 'entrega__reserva__cliente__nombre')
    readonly_fields = ('cargo_aplicado',)

@admin.register(TareaPreparacion)
class TareaPreparacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'orden', 'es_obligatoria')
    list_filter = ('categoria', 'es_obligatoria')
    search_fields = ('nombre', 'descripcion')
    ordering = ('categoria', 'orden', 'nombre')

@admin.register(PreparacionCabaña)
class PreparacionCabañaAdmin(admin.ModelAdmin):
    list_display = ('idPreparacion', 'reserva', 'estado', 'encargado', 'fecha_inicio', 'fecha_completacion')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('reserva__cliente__nombre', 'reserva__cabaña__nombre')
    readonly_fields = ('fecha_inicio',)

@admin.register(ItemPreparacionCompletado)
class ItemPreparacionCompletadoAdmin(admin.ModelAdmin):
    list_display = ('preparacion', 'tarea', 'completado', 'fecha_completado')
    list_filter = ('completado', 'tarea__categoria', 'preparacion')
    search_fields = ('tarea__nombre', 'preparacion__reserva__cabaña__nombre')

@admin.register(ReporteFaltantes)
class ReporteFaltantesAdmin(admin.ModelAdmin):
    list_display = ('idReporte', 'cabaña', 'encargado', 'faltantes_criticos', 'estado', 'fecha_creacion', 'fecha_atencion')
    list_filter = ('estado', 'faltantes_criticos', 'fecha_creacion')
    search_fields = ('cabaña__nombre', 'descripcion', 'encargado__username')
    readonly_fields = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'

