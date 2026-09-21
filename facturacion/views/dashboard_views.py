from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import PedidoCocina


@login_required(login_url='login')
def dashboard(request):
    pedidos_pendientes = PedidoCocina.objects.exclude(estado='ENTREGADO').count()
    return render(request, 'facturacion/dashboard.html', {
        'pedidos_pendientes': pedidos_pendientes,
    })