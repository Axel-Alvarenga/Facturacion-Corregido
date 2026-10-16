from .models import PedidoCocina, Venta


def pedidos_pendientes_nav(request):
    """Cuenta de pedidos sin entregar, disponible en todos los templates
    (se usa para el globito rojo junto a "Pedidos" en la navbar)."""
    if not request.user.is_authenticated:
        return {}
    return {'pedidos_pendientes_nav': PedidoCocina.objects.exclude(estado='ENTREGADO').count()}


def transferencias_pendientes_nav(request):
    """Cuenta de ventas por transferencia pendientes de confirmación.
    Se usa para el badge rojo en la navbar."""
    if not request.user.is_authenticated:
        return {}
    return {
        'transferencias_pendientes_nav': Venta.objects.filter(
            forma_pago='TRANSFERENCIA', estado='PENDIENTE'
        ).count()
    }