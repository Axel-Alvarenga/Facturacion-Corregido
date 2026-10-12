from django.db import models
from .cliente import Cliente
from .producto import Producto

TIPO_PAGO_CHOICES = [
    ('EFECTIVO', 'Efectivo'),
    ('CREDITO', 'Crédito'),
    ('TRANSFERENCIA', 'Transferencia'),
]


class Venta(models.Model):
    # PROTECT: no se puede borrar un cliente que ya tiene ventas registradas,
    # así nunca se pierde el historial de facturación por accidente.
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=50, choices=TIPO_PAGO_CHOICES)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Venta {self.id} - {self.cliente.nombre}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    # PROTECT: si se borra un producto que ya se vendió, se pierde el detalle
    # de esa factura. Mejor bloquear el borrado (o marcarlo inactivo a futuro).
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    # Precio copiado del producto en el momento de la venta: es una foto fija,
    # no una referencia viva a Producto.precio.
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)


class ItemVentaManual(models.Model):
    """Ítems cargados a mano en una venta, sin producto asociado del catálogo.
    Ejemplos: 'Recargo de pan', 'Plato roto', 'Propina', etc.
    El precio se carga manualmente en el momento de la venta.
    """
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='items_manuales',
    )
    descripcion = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.descripcion} - Gs. {self.precio}"