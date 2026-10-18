from django.conf import settings
from django.db import models
from .cliente import Cliente
from .venta import Venta


class PagoDeuda(models.Model):
    """Registro de cada pago que un cliente hace sobre su deuda.
    Se usa para calcular saldos pendientes reales por venta (FIFO)
    y para el KPI de 'crédito pendiente' en los informes.
    """
    FORMA_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='pagos',
    )
    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        related_name='pagos',
        null=True,
        blank=True,
        help_text='Venta a la que se aplica este pago (FIFO). '
                  'Null si es un pago a cuenta sin venta específica.',
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    forma_pago = models.CharField(
        max_length=20,
        choices=FORMA_PAGO_CHOICES,
        default='EFECTIVO',
        db_index=True,
        verbose_name='Forma de pago',
    )

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_deuda_registrados',
    )
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Pago de deuda'
        verbose_name_plural = 'Pagos de deuda'
        ordering = ['-fecha']

    def __str__(self):
        return (
            f"Pago de Gs. {self.monto:,.0f} - {self.cliente.nombre} "
            f"({self.fecha.strftime('%d/%m/%Y %H:%M')})"
        )