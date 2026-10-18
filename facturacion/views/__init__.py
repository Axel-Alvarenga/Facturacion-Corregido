from .auth_views import custom_login, custom_logout, extender_sesion
from .dashboard_views import dashboard
from .cliente_views import (
    cliente_list, cliente_create, cliente_update, cliente_delete, pagar_deuda,
)
from .producto_views import (
    producto_list, producto_create, producto_update, producto_delete,
)
from .venta_views import (
    crear_venta, confirmar_transferencia, venta_confirmada,
    ticket_venta, buscar_productos, venta_detalle_api, anular_venta,
)
from .pedido_views import (
    pedido_create, pedido_list, pedido_actualizar_estado,
)
from .informe_views import (
    informes_deudas,
    informes_deudas_pdf,
    informe_deuda_cliente_pdf,
    informes_ventas,
    informes_export_excel,
)
from .auditoria_views import (
    auditoria_list, auditoria_detalle, auditoria_export_excel,
)
from .caja_views import (
    caja_actual_api, caja_abrir_api, caja_cerrar_api,
    caja_movimiento_api, caja_list_api, caja_detalle_api,
)

__all__ = [
    'custom_login', 'custom_logout', 'extender_sesion', 'dashboard',
    'cliente_list', 'cliente_create', 'cliente_update', 'cliente_delete', 'pagar_deuda',
    'producto_list', 'producto_create', 'producto_update', 'producto_delete',
    'crear_venta', 'confirmar_transferencia', 'venta_confirmada',
    'ticket_venta', 'buscar_productos', 'venta_detalle_api', 'anular_venta',
    'pedido_create', 'pedido_list', 'pedido_actualizar_estado',
    'informes_deudas', 'informes_deudas_pdf', 'informe_deuda_cliente_pdf',
    'informes_ventas', 'informes_export_excel',
    'auditoria_list', 'auditoria_detalle', 'auditoria_export_excel',
    'caja_actual_api', 'caja_abrir_api', 'caja_cerrar_api',
    'caja_movimiento_api', 'caja_list_api', 'caja_detalle_api',
]