from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from ..models import Producto
from ..forms import ProductoForm


def _contexto_lista(request, form_modal=None, modal_activo=None, objeto_editar=None):
    """Construye el contexto de la lista de productos,
    opcionalmente con un modal abierto."""
    productos = Producto.objects.all()
    error_eliminar = None

    if request.GET.get('error') == 'no_se_puede_eliminar':
        error_eliminar = (
            f"No se puede eliminar \"{request.GET.get('nombre', '')}\": ya se vendió antes, "
            "y borrarlo perdería el detalle de esas ventas."
        )

    if modal_activo is None:
        abrir_modal = request.GET.get('abrir_modal', '').strip()
        if abrir_modal == 'crear':
            modal_activo = 'crear'
            form_modal = form_modal or ProductoForm()
        elif abrir_modal.startswith('editar_'):
            try:
                pk = int(abrir_modal.split('_', 1)[1])
                obj = Producto.objects.filter(pk=pk).first()
                if obj:
                    modal_activo = 'editar'
                    objeto_editar = obj
                    form_modal = form_modal or ProductoForm(instance=obj)
            except (ValueError, IndexError):
                pass

    return {
        'productos': productos,
        'error_eliminar': error_eliminar,
        'modal_activo': modal_activo,
        'form_modal': form_modal,
        'objeto_editar': objeto_editar,
    }


@login_required(login_url='login')
def producto_list(request):
    return render(request, 'facturacion/productos/producto_list.html',
                  _contexto_lista(request))


@login_required(login_url='login')
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect('producto_list')
        # Con errores: volvemos a renderizar la lista con el modal abierto
        messages.error(request, 'Revisá los errores del formulario.')
        return render(
            request,
            'facturacion/productos/producto_list.html',
            _contexto_lista(request, form_modal=form, modal_activo='crear'),
        )
    # GET: abrimos el modal vacío
    return redirect(f"{reverse('producto_list')}?abrir_modal=crear")


@login_required(login_url='login')
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado.')
            return redirect('producto_list')
        # Con errores: volvemos a renderizar la lista con el modal abierto
        messages.error(request, 'Revisá los errores del formulario.')
        return render(
            request,
            'facturacion/productos/producto_list.html',
            _contexto_lista(request, form_modal=form, modal_activo='editar',
                            objeto_editar=producto),
        )
    # GET: abrimos el modal con los datos
    return redirect(f"{reverse('producto_list')}?abrir_modal=editar_{pk}")


@login_required(login_url='login')
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            nombre = producto.nombre
            producto.delete()
            messages.success(request, f'Producto "{nombre}" eliminado.')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{producto.nombre}": ya se vendió antes.'
            )
            return redirect('producto_list')
    return redirect('producto_list')