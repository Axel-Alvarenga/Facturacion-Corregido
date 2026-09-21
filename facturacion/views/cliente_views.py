from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from ..models import Cliente, PagoDeuda
from ..forms import ClienteForm, PagoDeudaForm


@login_required(login_url='login')
def cliente_list(request):
    clientes = Cliente.objects.all()
    error_eliminar = None
    if request.GET.get('error') == 'no_se_puede_eliminar':
        error_eliminar = (
            f"No se puede eliminar a \"{request.GET.get('nombre', '')}\": ya tiene ventas "
            "registradas, y borrarlo perdería ese historial."
        )
    return render(request, 'facturacion/clientes/cliente_list.html', {
        'clientes': clientes,
        'total_clientes': clientes.count(),
        'clientes_con_deuda': clientes.filter(deuda__gt=0).count(),
        'monto_total_deuda': clientes.aggregate(total=Sum('deuda'))['total'] or Decimal('0.00'),
        'error_eliminar': error_eliminar,
    })


@login_required(login_url='login')
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'facturacion/clientes/cliente_form.html', {'form': form})


@login_required(login_url='login')
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('cliente_list')
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
            cliente.delete()
        except ProtectedError:
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
            return redirect('cliente_list')
    else:
        form = PagoDeudaForm(cliente=cliente)

    historial_pagos = cliente.pagos.all().order_by('-fecha')
    return render(request, 'facturacion/clientes/cliente_pagar_deuda.html', {
        'cliente': cliente,
        'form': form,
        'historial_pagos': historial_pagos,
    })