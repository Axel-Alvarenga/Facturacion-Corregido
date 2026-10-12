from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Cliente, Producto, Venta, DetalleVenta, ItemVentaManual


def _cliente_consumidor_final():
    """Cliente genérico para ventas sin cliente identificado."""
    cliente, _ = Cliente.objects.get_or_create(
        nombre='Consumidor Final',
        defaults={'telefono': '', 'tipo_pago': 'CONTADO'},
    )
    return cliente


@login_required(login_url='login')
def crear_venta(request):
    error = None

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '').strip()
        forma_pago = request.POST.get('forma_pago')
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        # Ítems manuales (opcionales)
        manual_descripciones = request.POST.getlist('manual_descripcion[]')
        manual_precios = request.POST.getlist('manual_precio[]')

        formas_validas = dict(Venta._meta.get_field('forma_pago').choices)

        if not productos_ids and not manual_descripciones:
            error = 'Agregá al menos un producto o un ítem manual.'
        elif forma_pago not in formas_validas:
            error = 'Forma de pago inválida.'

        if not error:
            if cliente_id:
                cliente = get_object_or_404(Cliente, id=cliente_id)
            else:
                cliente = _cliente_consumidor_final()

            try:
                with transaction.atomic():
                    total_real = Decimal('0.00')
                    detalles = []
                    manuales = []

                    # Productos del catálogo
                    for prod_id, cantidad_str in zip(productos_ids, cantidades):
                        cantidad = int(cantidad_str)
                        if cantidad < 1:
                            raise ValueError('Cantidad inválida')
                        producto = Producto.objects.get(id=prod_id)
                        total_real += producto.precio * cantidad
                        detalles.append((producto, cantidad, producto.precio))

                    # Ítems manuales
                    for desc, precio_str in zip(manual_descripciones, manual_precios):
                        desc = (desc or '').strip()
                        if not desc:
                            continue
                        try:
                            precio = Decimal(precio_str)
                        except (InvalidOperation, TypeError):
                            raise ValueError('Precio manual inválido')
                        if precio < 0:
                            raise ValueError('Precio manual no puede ser negativo')
                        total_real += precio
                        manuales.append((desc, precio))

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

                    for desc, precio in manuales:
                        ItemVentaManual.objects.create(
                            venta=venta,
                            descripcion=desc,
                            precio=precio,
                        )

                    if forma_pago == 'CREDITO':
                        cliente.deuda += total_real
                        cliente.save(update_fields=['deuda'])
            except (ValueError, Producto.DoesNotExist):
                error = 'Hubo un problema con los datos de la venta. Verificá e intentá de nuevo.'
            else:
                return redirect('informes')

    clientes = Cliente.objects.all().order_by('nombre')
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
        productos = Producto.objects.all().order_by('nombre')[:8]
    results = [
        {'id': p.id, 'nombre': p.nombre, 'precio': float(p.precio)}
        for p in productos
    ]
    return JsonResponse({'results': results})