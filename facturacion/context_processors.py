from .models import PedidoCocina


def pedidos_pendientes_nav(request):
    """Cuenta de pedidos sin entregar, disponible en todos los templates
    (se usa para el globito rojo junto a "Pedidos" en la navbar).
    Se resuelve con una sola consulta liviana (solo cuenta, no trae filas).
    """
    if not request.user.is_authenticated:
        return {}
    return {'pedidos_pendientes_nav': PedidoCocina.objects.exclude(estado='ENTREGADO').count()}
