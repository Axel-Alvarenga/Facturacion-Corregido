from .cliente import Cliente, PREFERENCIA_PAGO_CHOICES
from .producto import Producto
from .venta import Venta, DetalleVenta, ItemVentaManual, TIPO_PAGO_CHOICES
from .pago import PagoDeuda
from .pedido import PedidoCocina, DetallePedido

__all__ = [
    'Cliente',
    'PREFERENCIA_PAGO_CHOICES',
    'Producto',
    'Venta',
    'DetalleVenta',
    'ItemVentaManual',
    'TIPO_PAGO_CHOICES',
    'PagoDeuda',
    'PedidoCocina',
    'DetallePedido',
]