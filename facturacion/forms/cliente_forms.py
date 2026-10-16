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

    def clean_nombre(self):
        return (self.cleaned_data.get('nombre') or '').strip()

    def clean_nombre_local(self):
        valor = (self.cleaned_data.get('nombre_local') or '').strip()
        if not valor:
            raise forms.ValidationError('El local es obligatorio.')
        return valor

    def cliente_duplicado(self):
        """Devuelve el cliente duplicado (por nombre + local) si existe,
        excluyendo el propio (para el caso de edición)."""
        nombre = (self.cleaned_data.get('nombre') or '').strip().lower()
        local = (self.cleaned_data.get('nombre_local') or '').strip().lower()

        if not nombre or not local:
            return None

        qs = Cliente.objects.filter(
            nombre__iexact=nombre,
            nombre_local__iexact=local,
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        return qs.first()