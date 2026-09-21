from django.db import models
from .producto import Producto


class PedidoCocina(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PREPARACION', 'En preparación'),
        ('LISTO', 'Listo'),
        ('ENTREGADO', 'Entregado'),
    ]

    mesa_o_cliente = models.CharField(
        max_length=100,
        help_text='Mesa, nombre del cliente o referencia del pedido',
    )
    nota = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Pedido #{self.id} - {self.mesa_o_cliente}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        PedidoCocina,
        on_delete=models.CASCADE,
        related_name='items',
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    nota_item = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto}"