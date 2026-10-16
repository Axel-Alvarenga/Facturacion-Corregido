from django.db import models

# Preferencia de pago del cliente (forma en que paga)
PREFERENCIA_PAGO_CHOICES = [
    ('CONTADO', 'Contado'),
    ('CREDITO', 'Crédito'),
    ('TRANSFERENCIA', 'Transferencia'),
]

# Frecuencia con la que paga cuando es a crédito
FRECUENCIA_PAGO_CHOICES = [
    ('CONTADO', 'Contado'),
    ('SEMANAL', 'Semanal'),
    ('MENSUAL', 'Mensual'),
]


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    nombre_local = models.CharField(max_length=100, blank=True, null=True)
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
        # Formato "Nombre (Local)" para usarlo en listados y tickets
        if self.nombre_local:
            return f"{self.nombre} ({self.nombre_local})"
        return self.nombre

    def nombre_con_local(self):
        """Alias para usar en templates: {{ cliente.nombre_con_local }}"""
        return str(self)