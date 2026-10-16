from django.db import models
from django.conf import settings
from .cliente import Cliente
from .producto import Producto

TIPO_PAGO_CHOICES = [
    ('EFECTIVO', 'Efectivo'),
    ('CREDITO', 'Crédito'),
    ('TRANSFERENCIA', 'Transferencia'),
]

ESTADO_VENTA_CHOICES = [
    ('CONFIRMADA', 'Confirmada'),
    ('PENDIENTE', 'Pendiente de confirmación'),
]


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=50, choices=TIPO_PAGO_CHOICES)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Solo para ventas en EFECTIVO
    monto_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto pagado',
    )
    vuelto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Vuelto',
    )

    # Estado de la venta: para transferencias queda PENDIENTE
    # hasta que el usuario confirma que la recibió.
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_VENTA_CHOICES,
        default='CONFIRMADA',
        db_index=True,
    )
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_confirmadas',
    )

    def __str__(self):
        return f"Venta {self.id} - {self.cliente.nombre}"

    def es_transferencia_pendiente(self):
        return self.forma_pago == 'TRANSFERENCIA' and self.estado == 'PENDIENTE'

    def tiene_vuelto(self):
        return self.vuelto is not None and self.vuelto > 0


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)


class ItemVentaManual(models.Model):
    """Ítems cargados a mano en una venta, sin producto asociado del catálogo."""
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='items_manuales',
    )
    descripcion = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.descripcion} - Gs. {self.precio}"