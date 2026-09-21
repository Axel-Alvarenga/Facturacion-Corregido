from django.db import models

# Preferencia de pago del cliente (distinta de la forma de pago de una
# venta puntual): "Contado" es como suele hablarse en el mostrador de un
# cliente que siempre paga en el momento.
PREFERENCIA_PAGO_CHOICES = [
    ('CONTADO', 'Contado'),
    ('CREDITO', 'Crédito'),
    ('TRANSFERENCIA', 'Transferencia'),
]


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    nombre_local = models.CharField(max_length=100, blank=True, null=True)
    # Antes era un CharField libre pero el formulario lo mostraba como <select>
    # sin opciones (por eso se veía roto/flotando). Ahora usa las mismas
    # opciones de forma de pago, como preferencia del cliente.
    tipo_pago = models.CharField(
        max_length=50,
        choices=PREFERENCIA_PAGO_CHOICES,
        default='CONTADO',
        blank=True,
        null=True,
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    deuda = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.nombre