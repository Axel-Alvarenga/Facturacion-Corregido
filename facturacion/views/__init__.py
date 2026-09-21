from .auth_views import custom_login, custom_logout
from .dashboard_views import dashboard
from .cliente_views import (
    cliente_list,
    cliente_create,
    cliente_update,
    cliente_delete,
    pagar_deuda,
)
from .producto_views import (
    producto_list,
    producto_create,
    producto_update,
    producto_delete,
)
from .venta_views import crear_venta, buscar_productos
from .pedido_views import (
    pedido_create,
    pedido_list,
    pedido_actualizar_estado,
)
from .informe_views import (
    informes,
    informes_export_excel,
    _ventas_filtradas,
)

__all__ = [
    'custom_login',
    'custom_logout',
    'dashboard',
    'cliente_list',
    'cliente_create',
    'cliente_update',
    'cliente_delete',
    'pagar_deuda',
    'producto_list',
    'producto_create',
    'producto_update',
    'producto_delete',
    'crear_venta',
    'buscar_productos',
    'pedido_create',
    'pedido_list',
    'pedido_actualizar_estado',
    'informes',
    'informes_export_excel',
]