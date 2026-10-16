from django import forms
from ..models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'nombre_local', 'tipo_pago', 'frecuencia_pago', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_local': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
            'frecuencia_pago': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }