from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def cliente_required(view_func):
    """Decorador para verificar que el usuario es un cliente"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'cliente'):
            messages.error(request, 'Acceso denegado. Debe ser un cliente registrado.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def administrador_required(view_func):
    """Decorador para verificar que el usuario es administrador"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Acceso denegado. Se requieren permisos de administrador.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def encargado_required(view_func):
    """Decorador para verificar que el usuario es encargado"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Los encargados pueden ser staff o tener un grupo específico
        if not (request.user.is_staff or request.user.groups.filter(name='Encargados').exists()):
            messages.error(request, 'Acceso denegado. Se requieren permisos de encargado.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

