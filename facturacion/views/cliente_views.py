from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from ..models import Cliente, PagoDeuda, Venta, Caja, MovimientoCaja
from ..forms import ClienteForm, PagoDeudaForm


def _contexto_lista(request, form_modal=None, modal_activo=None, objeto_editar=None):
    clientes = Cliente.objects.all()
    error_eliminar = None

    if request.GET.get('error') == 'no_se_puede_eliminar':
        error_eliminar = (
            f"No se puede eliminar a \"{request.GET.get('nombre', '')}\": ya tiene ventas "
            "registradas, y borrarlo perdería ese historial."
        )

    if modal_activo is None:
        abrir_modal = request.GET.get('abrir_modal', '').strip()
        if abrir_modal == 'crear':
            modal_activo = 'crear'
            form_modal = form_modal or ClienteForm()
        elif abrir_modal.startswith('editar_'):
            try:
                pk = int(abrir_modal.split('_', 1)[1])
                obj = Cliente.objects.filter(pk=pk).first()
                if obj:
                    modal_activo = 'editar'
                    objeto_editar = obj
                    form_modal = form_modal or ClienteForm(instance=obj)
            except (ValueError, IndexError):
                pass

    return {
        'clientes': clientes,
        'total_clientes': clientes.count(),
        'clientes_con_deuda': clientes.filter(deuda__gt=0).count(),
        'monto_total_deuda': clientes.filter(deuda__gt=0).aggregate(total=Sum('deuda'))['total'] or Decimal('0.00'),
        'error_eliminar': error_eliminar,
        'modal_activo': modal_activo,
        'form_modal': form_modal,
        'objeto_editar': objeto_editar,
    }


@login_required(login_url='login')
def cliente_list(request):
    return render(request, 'facturacion/clientes/cliente_list.html',
                  _contexto_lista(request))


@login_required(login_url='login')
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        origen = request.POST.get('origen', '').strip()
        es_ajax = origen in ('venta', 'modal_listado')
        confirmar_duplicado = request.POST.get('confirmar_duplicado', '') == '1'

        if form.is_valid():
            duplicado = form.cliente_duplicado() if not confirmar_duplicado else None

            if duplicado and es_ajax:
                return JsonResponse({
                    'ok': False,
                    'duplicado': True,
                    'mensaje': f'Ya existe un cliente "{duplicado.nombre} ({duplicado.nombre_local})". ¿Confirmás que es otro distinto?',
                }, status=409)

            if duplicado and not es_ajax:
                messages.warning(
                    request,
                    f'Ya existe un cliente con el mismo nombre y local: '
                    f'"{duplicado.nombre} ({duplicado.nombre_local})". '
                    f'Si estás seguro, presioná "Confirmar de todos modos".'
                )
                return render(
                    request,
                    'facturacion/clientes/cliente_list.html',
                    _contexto_lista(
                        request,
                        form_modal=form,
                        modal_activo='crear',
                    ),
                )

            cliente = form.save()

            if origen == 'venta':
                return JsonResponse({
                    'ok': True,
                    'cliente': {
                        'id': cliente.id,
                        'nombre': cliente.nombre,
                        'nombre_local': cliente.nombre_local or '',
                        'tipo_pago': cliente.tipo_pago or 'CONTADO',
                        'nombre_display': str(cliente),
                    }
                })

            if origen == 'modal_listado':
                return JsonResponse({'ok': True, 'cliente_id': cliente.id})

            messages.success(request, f'Cliente "{cliente.nombre}" creado.')
            return redirect('cliente_list')

        if es_ajax:
            return JsonResponse({
                'ok': False,
                'errors': _form_errors_to_dict(form),
            }, status=400)

        messages.error(request, 'Revisá los errores del formulario.')
    else:
        form = ClienteForm()
    return render(request, 'facturacion/clientes/cliente_form.html', {'form': form})


@login_required(login_url='login')
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        origen = request.POST.get('origen', '').strip()
        es_ajax = origen == 'modal_listado'
        confirmar_duplicado = request.POST.get('confirmar_duplicado', '') == '1'

        if form.is_valid():
            duplicado = form.cliente_duplicado() if not confirmar_duplicado else None

            if duplicado and es_ajax:
                return JsonResponse({
                    'ok': False,
                    'duplicado': True,
                    'mensaje': f'Ya existe otro cliente "{duplicado.nombre} ({duplicado.nombre_local})". ¿Confirmás que no es un duplicado?',
                }, status=409)

            if duplicado and not es_ajax:
                messages.warning(
                    request,
                    f'Ya existe un cliente con el mismo nombre y local: '
                    f'"{duplicado.nombre} ({duplicado.nombre_local})". '
                    f'Si estás seguro, presioná "Guardar de todos modos".'
                )
                return render(
                    request,
                    'facturacion/clientes/cliente_list.html',
                    _contexto_lista(
                        request,
                        form_modal=form,
                        modal_activo='editar',
                        objeto_editar=cliente,
                    ),
                )

            cliente = form.save()

            if es_ajax:
                return JsonResponse({'ok': True, 'cliente_id': cliente.id})

            messages.success(request, f'Cliente "{cliente.nombre}" actualizado.')
            return redirect('cliente_list')

        if es_ajax:
            return JsonResponse({
                'ok': False,
                'errors': _form_errors_to_dict(form),
            }, status=400)

        messages.error(request, 'Revisá los errores del formulario.')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'facturacion/clientes/cliente_form.html', {
        'form': form,
        'object': cliente,
    })


@login_required(login_url='login')
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        try:
            nombre = cliente.nombre
            cliente.delete()
            messages.success(request, f'Cliente "{nombre}" eliminado.')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar a "{cliente.nombre}": tiene ventas registradas.'
            )
            return redirect(
                f"{reverse('cliente_list')}?error=no_se_puede_eliminar&nombre={cliente.nombre}"
            )
    return redirect('cliente_list')


@login_required(login_url='login')
def pagar_deuda(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if next_url and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = ''

    if request.method == 'POST':
        form = PagoDeudaForm(request.POST, cliente=cliente)
        if form.is_valid():
            monto_pago = form.cleaned_data['monto']
            forma_pago = request.POST.get('forma_pago', 'EFECTIVO').upper()
            if forma_pago not in ('EFECTIVO', 'TRANSFERENCIA'):
                forma_pago = 'EFECTIVO'

            if monto_pago > cliente.deuda and cliente.tipo_pago != 'CREDITO':
                messages.error(
                    request,
                    f'El monto (Gs. {monto_pago:,.0f}) supera la deuda actual '
                    f'(Gs. {cliente.deuda:,.0f}). Solo los clientes con '
                    f'preferencia "Crédito" pueden tener saldo a favor.'
                )
                return render(
                    request,
                    'facturacion/clientes/cliente_pagar_deuda.html',
                    {
                        'cliente': cliente,
                        'form': form,
                        'historial_pagos': cliente.pagos.all().order_by('-fecha'),
                        'next': next_url,
                    },
                )

            with transaction.atomic():
                pagos_creados = _aplicar_pago_fifo(
                    cliente, monto_pago, request.user, forma_pago,
                )

                cliente.deuda -= monto_pago
                cliente.save(update_fields=['deuda'])

                # ---- INTEGRACIÓN CON CAJA ----
                # Un solo MovimientoCaja consolidado (no uno por cada PagoDeuda)
                caja = Caja.caja_abierta()
                if caja:
                    MovimientoCaja.objects.create(
                        caja=caja,
                        tipo='PAGO',
                        forma_pago=forma_pago,
                        monto=monto_pago,
                        descripcion=f'Pago de deuda - {cliente.nombre} - {dict(PagoDeuda.FORMA_PAGO_CHOICES)[forma_pago]}',
                        usuario=request.user,
                        pago_deuda=pagos_creados[0] if pagos_creados else None,
                    )
                # ---- FIN INTEGRACIÓN ----

            messages.success(
                request,
                f'Pago de Gs. {monto_pago:,.0f} registrado para {cliente.nombre}.'
            )

            if next_url:
                return redirect(next_url)
            return redirect('informes_deudas')
    else:
        form = PagoDeudaForm(cliente=cliente)

    historial_pagos = cliente.pagos.all().order_by('-fecha')
    return render(request, 'facturacion/clientes/cliente_pagar_deuda.html', {
        'cliente': cliente,
        'form': form,
        'historial_pagos': historial_pagos,
        'next': next_url,
    })


def _aplicar_pago_fifo(cliente, monto_total, usuario, forma_pago='EFECTIVO'):
    """Aplica un pago a las ventas a crédito del cliente en orden FIFO.
    Crea un PagoDeuda por cada venta afectada.
    Devuelve la lista de PagoDeuda creados.
    """
    monto_restante = Decimal(monto_total)
    pagos_creados = []

    ventas_credito = (
        Venta.objects
        .filter(cliente=cliente, forma_pago='CREDITO', anulada=False)
        .order_by('fecha')
    )

    for venta in ventas_credito:
        if monto_restante <= 0:
            break

        pagado_venta = (
            PagoDeuda.objects
            .filter(venta=venta)
            .aggregate(total=Sum('monto'))['total']
            or Decimal('0.00')
        )
        saldo_venta = venta.total - pagado_venta

        if saldo_venta <= 0:
            continue

        monto_aplicar = min(monto_restante, saldo_venta)

        pago = PagoDeuda.objects.create(
            cliente=cliente,
            venta=venta,
            monto=monto_aplicar,
            forma_pago=forma_pago,
            registrado_por=usuario,
        )
        pagos_creados.append(pago)
        monto_restante -= monto_aplicar

    if monto_restante > 0:
        pago = PagoDeuda.objects.create(
            cliente=cliente,
            venta=None,
            monto=monto_restante,
            forma_pago=forma_pago,
            registrado_por=usuario,
            observacion='Saldo a favor (pago mayor a la deuda)',
        )
        pagos_creados.append(pago)

    return pagos_creados


def _form_errors_to_dict(form):
    """Convierte los errores del form a un dict {campo: [mensajes]}."""
    return {campo: [str(m) for m in errores] for campo, errores in form.errors.items()}