from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import (
    Cliente, Producto, Venta, DetalleVenta, ItemVentaManual,
    Caja, MovimientoCaja,
)


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
    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '').strip()
        forma_pago = request.POST.get('forma_pago')
        productos_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')

        manual_descripciones = request.POST.getlist('manual_descripcion[]')
        manual_precios = request.POST.getlist('manual_precio[]')

        monto_pagado_str = request.POST.get('monto_pagado', '').strip()

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

            if forma_pago == 'CREDITO' and cliente.nombre.strip().lower() == 'consumidor final':
                error = 'No se puede vender a crédito a "Consumidor Final". Asigná un cliente real.'

        if not error:
            try:
                with transaction.atomic():
                    total_real = Decimal('0.00')
                    detalles = []
                    manuales = []

                    for prod_id, cantidad_str in zip(productos_ids, cantidades):
                        cantidad = int(cantidad_str)
                        if cantidad < 1:
                            raise ValueError('Cantidad inválida')
                        producto = Producto.objects.get(id=prod_id)
                        total_real += producto.precio * cantidad
                        detalles.append((producto, cantidad, producto.precio))

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

                    monto_pagado = None
                    vuelto = None
                    if forma_pago == 'EFECTIVO':
                        try:
                            monto_pagado = Decimal(monto_pagado_str) if monto_pagado_str else total_real
                        except (InvalidOperation, TypeError):
                            monto_pagado = total_real
                        if monto_pagado < 0:
                            monto_pagado = total_real
                        if monto_pagado < total_real:
                            error = 'El monto pagado no puede ser menor al total.'
                            raise ValueError('Monto pagado menor al total')
                        vuelto = monto_pagado - total_real

                    estado_venta = 'PENDIENTE' if forma_pago == 'TRANSFERENCIA' else 'CONFIRMADA'

                    venta = Venta.objects.create(
                        cliente=cliente,
                        forma_pago=forma_pago,
                        total=total_real,
                        monto_pagado=monto_pagado,
                        vuelto=vuelto,
                        estado=estado_venta,
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

                    # ---- INTEGRACIÓN CON CAJA ----
                    caja = Caja.caja_abierta()
                    if caja:
                        MovimientoCaja.objects.create(
                            caja=caja,
                            tipo='VENTA',
                            forma_pago=forma_pago,
                            monto=total_real,
                            descripcion=f'Venta #{venta.id} - {venta.get_forma_pago_display()}',
                            usuario=request.user,
                            venta=venta,
                        )
                    # ---- FIN INTEGRACIÓN ----

            except (ValueError, Producto.DoesNotExist):
                if not error:
                    error = 'Hubo un problema con los datos de la venta. Verificá e intentá de nuevo.'

            if not error:
                if es_ajax:
                    return JsonResponse({
                        'ok': True,
                        'venta': {
                            'id': venta.id,
                            'total': float(venta.total),
                            'total_fmt': f'{venta.total:,.0f}',
                            'cliente': venta.cliente.nombre,
                            'forma_pago': venta.get_forma_pago_display(),
                            'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                            'ticket_url': f'/ventas/{venta.id}/ticket/',
                            'estado': venta.estado,
                            'es_pendiente': venta.estado == 'PENDIENTE',
                            'monto_pagado_fmt': f'{venta.monto_pagado:,.0f}' if venta.monto_pagado is not None else None,
                            'vuelto_fmt': f'{venta.vuelto:,.0f}' if venta.vuelto is not None else None,
                            'tiene_vuelto': venta.tiene_vuelto(),
                        }
                    })
                return redirect('venta_confirmada', venta_id=venta.id)

    if es_ajax:
        return JsonResponse({
            'ok': False,
            'error': error or 'Error desconocido.',
        }, status=400)

    clientes = Cliente.objects.all().order_by('nombre')
    productos = Producto.objects.all()
    context = {
        'clientes': clientes,
        'productos': productos,
    }
    if error:
        context['error'] = error
        messages.error(request, error)
    return render(request, 'facturacion/ventas/venta_form.html', context)


@login_required(login_url='login')
def confirmar_transferencia(request, venta_id):
    """Marca una venta por transferencia como recibida (CONFIRMADA)."""
    venta = get_object_or_404(Venta, pk=venta_id)

    if request.method == 'POST':
        if venta.forma_pago == 'TRANSFERENCIA' and venta.estado == 'PENDIENTE':
            venta.estado = 'CONFIRMADA'
            venta.fecha_confirmacion = timezone.now()
            venta.confirmado_por = request.user
            venta.save(update_fields=['estado', 'fecha_confirmacion', 'confirmado_por'])
            messages.success(
                request,
                f'Transferencia de la venta #{venta.id} (Gs. {venta.total:,.0f}) confirmada.'
            )
        else:
            messages.warning(
                request,
                f'La venta #{venta.id} no está pendiente de confirmación.'
            )

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('informes_ventas')


@login_required(login_url='login')
def venta_confirmada(request, venta_id):
    """Pantalla de éxito después de registrar una venta (fallback sin JS)."""
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'facturacion/ventas/venta_confirmada.html', {
        'venta': venta,
    })


@login_required(login_url='login')
def ticket_venta(request, venta_id):
    """Vista que renderiza el ticket para impresión (80mm)."""
    venta = get_object_or_404(Venta, pk=venta_id)
    return render(request, 'facturacion/ventas/ticket_venta.html', {
        'venta': venta,
    })


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


@login_required(login_url='login')
def venta_detalle_api(request, venta_id):
    """Devuelve el detalle completo de una venta en JSON, para el modal."""
    venta = get_object_or_404(
        Venta.objects.select_related('cliente'),
        pk=venta_id
    )

    detalles = []
    for d in venta.detalles.select_related('producto').all():
        detalles.append({
            'tipo': 'producto',
            'producto': d.producto.nombre,
            'cantidad': d.cantidad,
            'precio_unitario': float(d.precio_unitario),
            'precio_unitario_fmt': f'{d.precio_unitario:,.0f}',
            'subtotal': float(d.precio_unitario * d.cantidad),
            'subtotal_fmt': f'{d.precio_unitario * d.cantidad:,.0f}',
        })

    manuales = []
    for i in venta.items_manuales.all():
        manuales.append({
            'tipo': 'manual',
            'descripcion': i.descripcion,
            'precio': float(i.precio),
            'precio_fmt': f'{i.precio:,.0f}',
        })

    return JsonResponse({
        'ok': True,
        'venta': {
            'id': venta.id,
            'cliente': venta.cliente.nombre,
            'nombre_local': venta.cliente.nombre_local or '',
            'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
            'forma_pago': venta.get_forma_pago_display(),
            'forma_pago_raw': venta.forma_pago,
            'estado': venta.get_estado_display(),
            'estado_raw': venta.estado,
            'total': float(venta.total),
            'total_fmt': f'{venta.total:,.0f}',
            'monto_pagado_fmt': f'{venta.monto_pagado:,.0f}' if venta.monto_pagado is not None else None,
            'vuelto_fmt': f'{venta.vuelto:,.0f}' if venta.vuelto is not None else None,
            'tiene_vuelto': venta.tiene_vuelto(),
            'detalles': detalles,
            'items_manuales': manuales,
            'ticket_url': f'/ventas/{venta.id}/ticket/',
            'anulada': venta.anulada,
            'fecha_anulacion': venta.fecha_anulacion.strftime('%d/%m/%Y %H:%M') if venta.fecha_anulacion else None,
            'anulada_por': venta.anulada_por.username if venta.anulada_por else None,
            'motivo_anulacion': venta.motivo_anulacion or '',
            'puede_anularse': venta.puede_anularse()[0],
            'motivo_no_anulable': venta.puede_anularse()[1],
        }
    })


@login_required(login_url='login')
def anular_venta(request, venta_id):
    """Anula una venta (borrado lógico)."""
    if not request.user.is_superuser:
        messages.error(request, 'Solo los superusuarios pueden anular ventas.')
        return redirect('informes_ventas')

    venta = get_object_or_404(Venta.objects.select_related('cliente'), pk=venta_id)

    if request.method != 'POST':
        return redirect('informes_ventas')

    puede, motivo = venta.puede_anularse()
    if not puede:
        messages.error(request, motivo)
        return redirect('informes_ventas')

    motivo_anulacion = request.POST.get('motivo', '').strip()
    if not motivo_anulacion:
        messages.error(request, 'Tenés que indicar el motivo de la anulación.')
        return redirect('informes_ventas')

    with transaction.atomic():
        if venta.forma_pago == 'CREDITO':
            cliente = venta.cliente
            cliente.deuda -= venta.total
            cliente.save(update_fields=['deuda'])

        venta.anulada = True
        venta.fecha_anulacion = timezone.now()
        venta.anulada_por = request.user
        venta.motivo_anulacion = motivo_anulacion[:300]
        venta.save(update_fields=[
            'anulada', 'fecha_anulacion', 'anulada_por', 'motivo_anulacion',
        ])

        # Marcar movimientos de caja como anulados
        MovimientoCaja.objects.filter(venta=venta, anulado=False).update(
            anulado=True,
            fecha_anulacion=timezone.now(),
        )

    messages.success(
        request,
        f'Venta #{venta.id} anulada. Motivo: {motivo_anulacion}'
    )
    return redirect('informes_ventas')


@login_required(login_url='login')
def transferencias_pendientes_api(request):
    """Devuelve la lista de ventas por transferencia pendientes de confirmar."""
    ventas = (
        Venta.objects
        .filter(forma_pago='TRANSFERENCIA', estado='PENDIENTE', anulada=False)
        .select_related('cliente')
        .order_by('fecha')
    )

    data = []
    for v in ventas:
        data.append({
            'id': v.id,
            'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
            'cliente': v.cliente.nombre,
            'nombre_local': v.cliente.nombre_local or '',
            'total': float(v.total),
            'total_fmt': f'{v.total:,.0f}',
            'confirmar_url': f'/ventas/{v.id}/confirmar-transferencia/',
        })

    return JsonResponse({'ok': True, 'ventas': data, 'total': len(data)})