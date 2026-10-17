from django import forms
from ..models import PagoDeuda


class PagoDeudaForm(forms.ModelForm):
    class Meta:
        model = PagoDeuda
        fields = ['monto']
        widgets = {
            'monto': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Ingrese monto a abonar'}
            )
        }

    def __init__(self, *args, cliente=None, **kwargs):
        # El cliente se pasa desde la vista para poder validar el monto
        # contra su deuda actual (ver clean_monto).
        self.cliente = cliente
        super().__init__(*args, **kwargs)

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto <= 0:
            raise forms.ValidationError('El monto a abonar debe ser mayor a cero.')

        # Solo bloquear pago mayor a la deuda si el cliente NO es CREDITO.
        # Los clientes CREDITO pueden tener saldo a favor.
        if (
            self.cliente is not None
            and self.cliente.tipo_pago != 'CREDITO'
            and monto > self.cliente.deuda
        ):
            raise forms.ValidationError(
                f'El monto no puede superar la deuda actual '
                f'(Gs. {self.cliente.deuda:,.0f}).'
            )
        return monto