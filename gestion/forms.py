from django import forms
from .models import (
    Cliente, Reserva, Cabaña, Encuesta, Pago,
    Implemento, PrestamoImplemento, Mantenimiento
)
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class RegistroClienteForm(UserCreationForm):
    """Formulario de registro para clientes"""
    nombre = forms.CharField(max_length=200, required=True)
    telefono = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=True)
    direccion = forms.CharField(widget=forms.Textarea, required=True)
    tipoCliente = forms.CharField(max_length=50, required=False, initial='Regular')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            cliente = Cliente.objects.create(
                nombre=self.cleaned_data['nombre'],
                telefono=self.cleaned_data['telefono'],
                email=self.cleaned_data['email'],
                direccion=self.cleaned_data['direccion'],
                tipoCliente=self.cleaned_data.get('tipoCliente', 'Regular'),
                usuario=user
            )
        return user


class ReservaForm(forms.ModelForm):
    """Formulario para solicitar reservas"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fecha mínima: 4 días después de hoy
        hoy = timezone.now().date()
        fecha_minima = hoy + timedelta(days=4)
        self.fields['fechaInicio'].widget.attrs['min'] = fecha_minima.isoformat()
        self.fields['fechaFin'].widget.attrs['min'] = fecha_minima.isoformat()

    class Meta:
        model = Reserva
        fields = ['cabaña', 'fechaInicio', 'fechaFin', 'numPersonas', 'comentarios']
        widgets = {
            'fechaInicio': forms.DateInput(attrs={'type': 'date'}),
            'fechaFin': forms.DateInput(attrs={'type': 'date'}),
            'comentarios': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_fechaInicio(self):
        fecha_inicio = self.cleaned_data.get('fechaInicio')
        if fecha_inicio:
            hoy = timezone.now().date()
            fecha_minima = hoy + timedelta(days=4)
            if fecha_inicio < fecha_minima:
                raise forms.ValidationError(
                    f'Debes solicitar la reserva con al menos 4 días de anticipación. '
                    f'La fecha mínima permitida es {fecha_minima.strftime("%d/%m/%Y")}.'
                )
        return fecha_inicio


class EncuestaForm(forms.ModelForm):
    """Formulario para completar encuestas"""
    class Meta:
        model = Encuesta
        fields = ['calificacion', 'comentarios']
        widgets = {
            'comentarios': forms.Textarea(attrs={'rows': 4}),
        }


class PagoForm(forms.ModelForm):
    """Formulario para registrar pagos"""
    class Meta:
        model = Pago
        fields = ['reserva', 'monto', 'metodo', 'fechaPago', 'comprobante']
        widgets = {
            'fechaPago': forms.DateInput(attrs={'type': 'date'}),
        }


class PrestamoImplementoForm(forms.ModelForm):
    """Formulario para solicitar préstamos de implementos"""
    class Meta:
        model = PrestamoImplemento
        fields = ['implemento', 'cantidad', 'fechaPrestamo']
        widgets = {
            'fechaPrestamo': forms.DateInput(attrs={'type': 'date'}),
        }


class MantenimientoForm(forms.ModelForm):
    """Formulario para registrar mantenimientos"""
    class Meta:
        model = Mantenimiento
        fields = ['cabaña', 'tipo', 'descripcion', 'fechaProgramada']
        widgets = {
            'fechaProgramada': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }


class ImplementoForm(forms.ModelForm):
    """Formulario para gestionar implementos"""
    class Meta:
        model = Implemento
        fields = ['nombre', 'descripcion', 'cantidadTotal', 'cantidadDisponible', 'estado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

