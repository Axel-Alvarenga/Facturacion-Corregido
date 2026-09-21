from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Cliente, Producto, Venta, DetalleVenta
from ..forms import VentaForm  # noqa: F401 (por si se usa después)


@login_required(login_url='login')
def crear_venta(request):
    error = None

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        forma_pago = request.POST.get('forma_pago')
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        # OJO: ya NO leemos 'precio[]' ni 'total' del POST. Esos vienen del
        # navegador y alguien podría editarlos. El precio de cada producto y
        # el total se recalculan siempre acá, del lado del servidor.

        formas_validas = dict(Venta._meta.get_field('forma_pago').choices)

        if not cliente_id:
            error = 'Seleccioná un cliente.'
        elif not productos_ids:
            error = 'Agregá al menos un producto.'
        elif forma_pago not in formas_validas:
            error = 'Forma de pago inválida.'

        if not error:
            cliente = get_object_or_404(Cliente, id=cliente_id)
            try:
                with transaction.atomic():
                    total_real = Decimal('0.00')
                    detalles = []

                    for prod_id, cantidad_str in zip(productos_ids, cantidades):
                        cantidad = int(cantidad_str)
                        if cantidad < 1:
                            raise ValueError('Cantidad inválida')
                        producto = Producto.objects.get(id=prod_id)
                        total_real += producto.precio * cantidad
                        detalles.append((producto, cantidad, producto.precio))

                    venta = Venta.objects.create(
                        cliente=cliente,
                        forma_pago=forma_pago,
                        total=total_real,
                    )

                    for producto, cantidad, precio in detalles:
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio,
                        )

                    if forma_pago == 'CREDITO':
                        cliente.deuda += total_real
                        cliente.save(update_fields=['deuda'])
            except (ValueError, Producto.DoesNotExist):
                error = 'Hubo un problema con los productos de la venta. Verificá e intentá de nuevo.'
            else:
                return redirect('informes')

    clientes = Cliente.objects.all()
    productos = Producto.objects.all()
    context = {
        'clientes': clientes,
        'productos': productos,
    }
    if error:
        context['error'] = error
    return render(request, 'facturacion/ventas/venta_form.html', context)


@login_required(login_url='login')
def buscar_productos(request):
    query = request.GET.get('q', '').strip()
    if query:
        productos = Producto.objects.filter(nombre__icontains=query).order_by('nombre')[:10]
    else:
        # Sin texto todavía: mostramos algunas opciones para elegir de una.
        productos = Producto.objects.all().order_by('nombre')[:8]
    results = [
        {'id': p.id, 'nombre': p.nombre, 'precio': float(p.precio)}
        for p in productos
    ]
    return JsonResponse({'results': results})