from django.contrib import admin
from .models import (
    Cliente, Reserva, Cabaña, Encuesta, Pago,
    Implemento, PrestamoImplemento, Mantenimiento,
    Notificacion, ChecklistInventario, EntregaCabaña, ItemFaltante, ItemVerificacion
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

@admin.register(Encuesta)
class EncuestaAdmin(admin.ModelAdmin):
    list_display = ('idEncuesta', 'reserva', 'calificacion', 'fecha')
    list_filter = ('calificacion', 'fecha')

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

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('idMantenimiento', 'cabaña', 'tipo', 'fechaProgramada', 'estado')
    list_filter = ('tipo', 'estado')

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

@admin.register(ItemFaltante)
class ItemFaltanteAdmin(admin.ModelAdmin):
    list_display = ('idItemFaltante', 'entrega', 'item_checklist', 'cantidad_faltante')
    list_filter = ('entrega', 'item_checklist')
    search_fields = ('item_checklist__nombre_item',)



