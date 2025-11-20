from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro_cliente, name='registro_cliente'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Módulo Cliente
    path('cliente/', views.portal_cliente, name='portal_cliente'),
    path('cliente/solicitar-reserva/', views.solicitar_reserva, name='solicitar_reserva'),
    path('cliente/mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cliente/confirmar-reserva/<int:reserva_id>/', views.confirmar_reserva_cliente, name='confirmar_reserva_cliente'),
    path('cliente/checklist-entrega/<int:reserva_id>/', views.checklist_entrega, name='checklist_entrega'),
    path('cliente/encuesta/<int:reserva_id>/', views.completar_encuesta, name='completar_encuesta'),
    path('cliente/solicitar-prestamo/', views.solicitar_prestamo, name='solicitar_prestamo'),

    # Módulo Administrador
    path('administrador/dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('administrador/reservas/', views.gestion_reservas, name='gestion_reservas'),
    path('administrador/reservas/<int:reserva_id>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('administrador/reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('administrador/pagos/', views.registro_pagos, name='registro_pagos'),
    path('administrador/reportes/', views.reportes_generales, name='reportes_generales'),
    path('administrador/clientes/', views.gestion_clientes, name='gestion_clientes'),
    path('administrador/encuestas/', views.visualizar_encuestas, name='visualizar_encuestas'),
    path('administrador/mantenimiento/', views.supervisar_mantenimiento, name='supervisar_mantenimiento'),
    path('administrador/incidentes/', views.gestion_incidentes, name='gestion_incidentes'),
    path('administrador/historial-entregas/', views.historial_entregas, name='historial_entregas'),

    # Módulo Encargado
    path('encargado/dashboard/', views.dashboard_encargado, name='dashboard_encargado'),
    path('encargado/inventario/', views.inventario_cabañas, name='inventario_cabañas'),
    path('encargado/mantenimiento/', views.gestion_mantenimiento, name='gestion_mantenimiento'),
    path('encargado/mantenimiento/<int:mantenimiento_id>/finalizar/', views.finalizar_mantenimiento, name='finalizar_mantenimiento'),
    path('encargado/prestamos/', views.prestamos_implementos, name='prestamos_implementos'),
    path('encargado/prestamos/<int:prestamo_id>/devolucion/', views.registrar_devolucion, name='registrar_devolucion'),
    path('encargado/estado-cabañas/', views.estado_cabañas, name='estado_cabañas'),
    path('encargado/preparar-cabañas/', views.preparar_cabañas, name='preparar_cabañas'),
    path('encargado/preparacion-cabaña/<int:reserva_id>/', views.preparacion_cabaña, name='preparacion_cabaña'),
    path('encargado/checklist-entrega/<int:reserva_id>/', views.checklist_entrega_encargado, name='checklist_entrega_encargado'),
    path('encargado/verificacion-devolucion/<int:reserva_id>/', views.verificacion_devolucion, name='verificacion_devolucion'),
]

