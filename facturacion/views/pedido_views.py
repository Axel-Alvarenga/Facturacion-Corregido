from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Producto, PedidoCocina, DetallePedido


@login_required(login_url='login')
def pedido_create(request):
    error = None

    if request.method == 'POST':
        mesa_o_cliente = request.POST.get('mesa_o_cliente', '').strip()
        nota = request.POST.get('nota', '').strip()
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        notas_item = request.POST.getlist('nota_item[]')

        if not mesa_o_cliente:
            error = 'Indicá una mesa, nombre o referencia para el pedido.'
        elif not productos_ids:
            error = 'Agregá al menos un producto al pedido.'

        if not error:
            try:
                with transaction.atomic():
                    pedido = PedidoCocina.objects.create(
                        mesa_o_cliente=mesa_o_cliente,
                        nota=nota,
                    )
                    for i, (prod_id, cantidad_str) in enumerate(zip(productos_ids, cantidades)):
                        cantidad = int(cantidad_str)
                        if cantidad < 1:
                            raise ValueError('Cantidad inválida')
                        producto = Producto.objects.get(id=prod_id)
                        DetallePedido.objects.create(
                            pedido=pedido,
                            producto=producto,
                            cantidad=cantidad,
                            nota_item=notas_item[i] if i < len(notas_item) else '',
                        )
            except (ValueError, Producto.DoesNotExist):
                error = 'Hubo un problema con los productos del pedido. Verificá e intentá de nuevo.'
            else:
                return redirect('pedido_list')

    productos = Producto.objects.all().order_by('nombre')
    context = {'productos': productos}
    if error:
        context['error'] = error
    return render(request, 'facturacion/pedidos/pedido_form.html', context)


@login_required(login_url='login')
def pedido_list(request):
    pedidos = PedidoCocina.objects.prefetch_related('items__producto').exclude(estado='ENTREGADO')
    return render(request, 'facturacion/pedidos/pedido_list.html', {'pedidos': pedidos})


@login_required(login_url='login')
def pedido_actualizar_estado(request, pk, nuevo_estado):
    pedido = get_object_or_404(PedidoCocina, pk=pk)
    estados_validos = dict(PedidoCocina.ESTADO_CHOICES)
    if request.method == 'POST' and nuevo_estado in estados_validos:
        pedido.estado = nuevo_estado
        pedido.save(update_fields=['estado'])
    return redirect('pedido_list')