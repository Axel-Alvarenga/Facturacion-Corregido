from django.conf import settings
from django.db import models
from decimal import Decimal


class Caja(models.Model):
    """Representa un turno de caja (apertura y cierre).
    Solo puede haber una caja abierta a la vez.
    """
    ESTADO_CHOICES = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    ]

    fecha_apertura = models.DateTimeField(auto_now_add=True, db_index=True)
    monto_apertura = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Monto inicial en caja',
    )
    abierta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cajas_abiertas',
    )

    fecha_cierre = models.DateTimeField(null=True, blank=True, db_index=True)
    monto_cierre_real = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Monto real contado al cerrar',
    )
    monto_cierre_esperado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Monto esperado calculado',
    )
    diferencia = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Diferencia (real - esperado)',
    )
    cerrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cajas_cerradas',
    )

    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES,
        default='ABIERTA', db_index=True,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Caja #{self.id} - {self.get_estado_display()} - {self.fecha_apertura:%d/%m/%Y %H:%M}"

    @classmethod
    def caja_abierta(cls):
        """Devuelve la caja abierta actual (o None)."""
        return cls.objects.filter(estado='ABIERTA').first()

    def calcular_totales(self):
        """Calcula los totales de la caja. Separa efectivo (físico) de transferencias.
        Las transferencias PENDIENTES no suman al total en banco.
        """
        movs = self.movimientos.filter(anulado=False)

        # --- EFECTIVO (físico) ---
        ventas_efectivo = sum(
            (m.monto for m in movs if m.tipo == 'VENTA' and m.forma_pago == 'EFECTIVO'),
            Decimal('0.00'),
        )
        pagos_efectivo = sum(
            (m.monto for m in movs if m.tipo == 'PAGO' and m.forma_pago == 'EFECTIVO'),
            Decimal('0.00'),
        )
        ingresos = sum(
            (m.monto for m in movs if m.tipo == 'INGRESO'),
            Decimal('0.00'),
        )
        retiros = sum(
            (m.monto for m in movs if m.tipo == 'RETIRO'),
            Decimal('0.00'),
        )

        esperado = self.monto_apertura + ventas_efectivo + pagos_efectivo + ingresos - retiros

        # --- TRANSFERENCIAS (digital) ---
        # Confirmadas: ventas que ya se marcaron como recibidas + pagos de deuda
        ventas_transf_confirmadas = sum(
            (m.monto for m in movs
             if m.tipo == 'VENTA' and m.forma_pago == 'TRANSFERENCIA'
             and m.venta and m.venta.estado == 'CONFIRMADA'),
            Decimal('0.00'),
        )
        pagos_transf_confirmados = sum(
            (m.monto for m in movs if m.tipo == 'PAGO' and m.forma_pago == 'TRANSFERENCIA'),
            Decimal('0.00'),
        )
        
        total_transferencias = ventas_transf_confirmadas + pagos_transf_confirmados

        # Pendientes: ventas por transferencia que aún no se confirmaron
        ventas_transf_pendientes = sum(
            (m.monto for m in movs
             if m.tipo == 'VENTA' and m.forma_pago == 'TRANSFERENCIA'
             and m.venta and m.venta.estado == 'PENDIENTE'),
            Decimal('0.00'),
        )

        return {
            'monto_apertura': self.monto_apertura,
            'ventas_efectivo': ventas_efectivo,
            'pagos_efectivo': pagos_efectivo,
            'ingresos': ingresos,
            'retiros': retiros,
            'esperado': esperado,
            # Transferencias
            'ventas_transferencia': ventas_transf_confirmadas,
            'pagos_transferencia': pagos_transf_confirmados,
            'total_transferencias': total_transferencias,
            'transferencias_pendientes': ventas_transf_pendientes,
        }


class MovimientoCaja(models.Model):
    """Movimiento individual dentro de una caja:
    - VENTA: venta en efectivo (suma al esperado)
    - PAGO: pago de deuda en efectivo (suma al esperado)
    - INGRESO: aporte manual de efectivo (suma al esperado)
    - RETIRO: extracción manual de efectivo (resta del esperado)
    """
    TIPO_CHOICES = [
        ('VENTA', 'Venta'),
        ('PAGO', 'Pago de deuda'),
        ('INGRESO', 'Ingreso manual'),
        ('RETIRO', 'Retiro manual'),
    ]

    caja = models.ForeignKey(
        Caja, on_delete=models.CASCADE,
        related_name='movimientos',
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, db_index=True)
    forma_pago = models.CharField(
        max_length=20, blank=True,
        help_text='EFECTIVO / CREDITO / TRANSFERENCIA (solo para VENTA y PAGO)',
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=300, blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimientos_caja',
    )

    venta = models.ForeignKey(
        'Venta', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='movimientos_caja',
    )
    pago_deuda = models.ForeignKey(
        'PagoDeuda', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='movimientos_caja',
    )

    anulado = models.BooleanField(default=False, db_index=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Movimiento de caja'
        verbose_name_plural = 'Movimientos de caja'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - Gs. {self.monto} - {self.fecha:%d/%m/%Y %H:%M}"