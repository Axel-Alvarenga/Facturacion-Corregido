from django.db import models

PREFERENCIA_PAGO_CHOICES = [
    ('CONTADO', 'Contado'),
    ('CREDITO', 'Crédito'),
    ('TRANSFERENCIA', 'Transferencia'),
]

FRECUENCIA_PAGO_CHOICES = [
    ('CONTADO', 'Contado'),
    ('SEMANAL', 'Semanal'),
    ('MENSUAL', 'Mensual'),
]


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    # nombre_local ahora es OBLIGATORIO para poder diferenciar clientes
    # con el mismo nombre. Si el cliente no tiene local, se usa "Particular"
    # o similar (según lo que cargue el usuario).
    nombre_local = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        default='',
        verbose_name='Local',
    )
    tipo_pago = models.CharField(
        max_length=50,
        choices=PREFERENCIA_PAGO_CHOICES,
        default='CONTADO',
        blank=True,
        null=True,
    )
    frecuencia_pago = models.CharField(
        max_length=20,
        choices=FRECUENCIA_PAGO_CHOICES,
        default='CONTADO',
        blank=True,
        null=True,
        verbose_name='Frecuencia de pago',
        help_text='Con qué frecuencia paga cuando tiene deuda (semanal, mensual)',
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    deuda = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        # Siempre formatear como "Nombre (Local)"
        return f"{self.nombre} ({self.nombre_local})"

    def nombre_con_local(self):
        return str(self)