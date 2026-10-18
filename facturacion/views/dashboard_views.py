from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import PedidoCocina, Caja


@login_required(login_url='login')
def dashboard(request):
    pedidos_pendientes = PedidoCocina.objects.exclude(estado='ENTREGADO').count()

    caja_abierta = Caja.caja_abierta()
    caja_ultima_cerrada = None
    caja_totales = None
    caja_movs_count = 0

    if caja_abierta:
        caja_totales = caja_abierta.calcular_totales()
        caja_movs_count = caja_abierta.movimientos.filter(anulado=False).count()
    else:
        caja_ultima_cerrada = (
            Caja.objects
            .filter(estado='CERRADA')
            .order_by('-fecha_cierre')
            .first()
        )

    return render(request, 'facturacion/dashboard.html', {
        'pedidos_pendientes': pedidos_pendientes,
        'caja_abierta': caja_abierta,
        'caja_ultima_cerrada': caja_ultima_cerrada,
        'caja_totales': caja_totales,
        'caja_movs_count': caja_movs_count,
    })