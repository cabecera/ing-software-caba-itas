from django.contrib import admin
from .models import (
    Cliente, Reserva, Cabaña, Encuesta, Pago,
    Implemento, PrestamoImplemento, Mantenimiento,
    Notificacion
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('idCliente', 'nombre', 'telefono', 'email', 'tipoCliente')
    search_fields = ('nombre', 'email', 'telefono')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('idReserva', 'cliente', 'cabaña', 'fechaInicio', 'fechaFin', 'estado', 'montoCotizado')
    list_filter = ('estado', 'fechaInicio')
    search_fields = ('cliente__nombre', 'cabaña__nombre')

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



