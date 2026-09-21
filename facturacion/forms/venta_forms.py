from django import forms
from ..models import Venta


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'forma_pago', 'total']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'total': forms.NumberInput(attrs={'class': 'form-control'}),
        }