from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from ..models import Producto
from ..forms import ProductoForm


@login_required(login_url='login')
def producto_list(request):
    productos = Producto.objects.all()
    error_eliminar = None
    if request.GET.get('error') == 'no_se_puede_eliminar':
        error_eliminar = (
            f"No se puede eliminar \"{request.GET.get('nombre', '')}\": ya se vendió antes, "
            "y borrarlo perdería el detalle de esas ventas."
        )
    return render(request, 'facturacion/productos/producto_list.html', {
        'productos': productos,
        'error_eliminar': error_eliminar,
    })


@login_required(login_url='login')
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('producto_list')
    else:
        form = ProductoForm()
    return render(request, 'facturacion/productos/producto_form.html', {'form': form})


@login_required(login_url='login')
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('producto_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'facturacion/productos/producto_form.html', {'form': form})


@login_required(login_url='login')
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            producto.delete()
        except ProtectedError:
            return redirect(
                f"{reverse('producto_list')}?error=no_se_puede_eliminar&nombre={producto.nombre}"
            )
    return redirect('producto_list')