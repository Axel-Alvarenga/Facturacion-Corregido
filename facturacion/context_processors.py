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
            forma_pago='TRANSFERENCIA', estado='PENDIENTE', anulada=False
        ).count()
    }


def cierre_config(request):
    """Inyecta la configuración de cierre automático en el contexto.
    Incluye EXTENSION_HASTA para que el JS sepa si hay una extensión activa
    y no muestre el aviso de nuevo al navegar entre módulos."""
    from django.conf import settings

    extension_hasta = ''
    if hasattr(request, 'session'):
        extension_hasta = request.session.get('extension_hasta', '') or ''

    return {
        'CIERRE_SISTEMA_HORA': getattr(settings, 'CIERRE_SISTEMA_HORA', 20),
        'APERTURA_SISTEMA_HORA': getattr(settings, 'APERTURA_SISTEMA_HORA', 6),
        'AVISO_CIERRE_MINUTOS_ANTES': getattr(settings, 'AVISO_CIERRE_MINUTOS_ANTES', 5),
        'EXTENSION_HASTA': extension_hasta,
    }