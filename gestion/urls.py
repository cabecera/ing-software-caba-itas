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
    path('administrador/calendario/', views.calendario_disponibilidad, name='calendario_disponibilidad'),
    path('administrador/reservas/', views.gestion_reservas, name='gestion_reservas'),
    path('administrador/reservas/<int:reserva_id>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('administrador/reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('administrador/cabañas/', views.gestion_cabañas, name='gestion_cabañas'),
    path('administrador/clientes/', views.gestion_clientes, name='gestion_clientes'),
    path('administrador/pagos/', views.registro_pagos, name='registro_pagos'),
    path('administrador/notificaciones/', views.panel_notificaciones, name='panel_notificaciones'),
    path('administrador/reportes-faltantes/', views.atender_reportes_faltantes, name='atender_reportes_faltantes'),

    # Módulo Encargado
    path('encargado/dashboard/', views.dashboard_encargado, name='dashboard_encargado'),
    path('encargado/preparar-cabañas/', views.preparar_cabañas, name='preparar_cabañas'),
    path('encargado/preparacion-cabaña/<int:reserva_id>/', views.preparacion_cabaña, name='preparacion_cabaña'),
    path('encargado/inventario/', views.inventario_cabañas, name='inventario_cabañas'),
    path('encargado/reporte-faltantes/', views.reporte_faltantes, name='reporte_faltantes'),
    path('encargado/notificaciones/', views.notificaciones_encargado, name='notificaciones_encargado'),
]

