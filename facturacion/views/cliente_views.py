from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from ..models import Cliente, PagoDeuda
from ..forms import ClienteForm, PagoDeudaForm


def _contexto_lista(request, form_modal=None, modal_activo=None, objeto_editar=None):
    """Construye el contexto de la lista de clientes,
    opcionalmente con un modal abierto."""
    clientes = Cliente.objects.all()
    error_eliminar = None

    if request.GET.get('error') == 'no_se_puede_eliminar':
        error_eliminar = (
            f"No se puede eliminar a \"{request.GET.get('nombre', '')}\": ya tiene ventas "
            "registradas, y borrarlo perdería ese historial."
        )

    # Si no nos pasaron form, pero la URL trae ?abrir_modal=..., lo armamos
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
        'monto_total_deuda': clientes.aggregate(total=Sum('deuda'))['total'] or Decimal('0.00'),
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
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" creado correctamente.')
            return redirect('cliente_list')
        # Con errores: volvemos a renderizar la lista con el modal abierto
        messages.error(request, 'Revisá los errores del formulario.')
        return render(
            request,
            'facturacion/clientes/cliente_list.html',
            _contexto_lista(request, form_modal=form, modal_activo='crear'),
        )
    # GET: abrimos el modal vacío
    return redirect(f"{reverse('cliente_list')}?abrir_modal=crear")


@login_required(login_url='login')
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" actualizado.')
            return redirect('cliente_list')
        # Con errores: volvemos a renderizar la lista con el modal abierto
        messages.error(request, 'Revisá los errores del formulario.')
        return render(
            request,
            'facturacion/clientes/cliente_list.html',
            _contexto_lista(request, form_modal=form, modal_activo='editar',
                            objeto_editar=cliente),
        )
    # GET: abrimos el modal con los datos
    return redirect(f"{reverse('cliente_list')}?abrir_modal=editar_{pk}")


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
    if request.method == 'POST':
        form = PagoDeudaForm(request.POST, cliente=cliente)
        if form.is_valid():
            with transaction.atomic():
                pago = form.save(commit=False)
                pago.cliente = cliente
                pago.save()
                cliente.deuda -= pago.monto
                cliente.save(update_fields=['deuda'])
            messages.success(
                request,
                f'Pago de Gs. {pago.monto:,.0f} registrado para {cliente.nombre}.'
            )
            return redirect('cliente_list')
    else:
        form = PagoDeudaForm(cliente=cliente)

    historial_pagos = cliente.pagos.all().order_by('-fecha')
    return render(request, 'facturacion/clientes/cliente_pagar_deuda.html', {
        'cliente': cliente,
        'form': form,
        'historial_pagos': historial_pagos,
    })