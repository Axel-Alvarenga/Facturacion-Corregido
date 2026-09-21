/* =========================================================
   Comedor A.R.M. - Formulario de nuevo pedido a cocina
   - Buscador de productos con AJAX (muestra sugerencias al enfocar)
   - Agregar productos a la tabla
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const inputProd = document.getElementById('buscar-prod');
    const resProd = document.getElementById('resultados-prod');
    const cuerpoTabla = document.getElementById('cuerpo-tabla');
    const formPedido = document.getElementById('form-pedido');

    function mostrarSugerencias(query) {
        fetch('/api/buscar-productos/?q=' + encodeURIComponent(query))
            .then(res => res.json())
            .then(data => {
                resProd.innerHTML = '';
                data.results.forEach(p => {
                    const item = document.createElement('a');
                    item.className = 'list-group-item list-group-item-action';
                    item.style.cursor = 'pointer';
                    item.textContent = p.nombre;
                    item.onclick = function (e) {
                        e.preventDefault();
                        agregarFila(p);
                        resProd.innerHTML = '';
                        inputProd.value = '';
                    };
                    resProd.appendChild(item);
                });
            });
    }

    // Al hacer foco (sin escribir nada) ya muestra sugerencias
    inputProd.addEventListener('focus', function () {
        if (this.value.trim().length === 0) mostrarSugerencias('');
    });
    inputProd.addEventListener('input', function () {
        mostrarSugerencias(this.value.trim());
    });

    // Cerrar sugerencias al hacer click fuera
    document.addEventListener('click', function (e) {
        if (!resProd.contains(e.target) && e.target !== inputProd) {
            resProd.innerHTML = '';
        }
    });

    function agregarFila(producto) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                ${producto.nombre}
                <input type="hidden" name="producto_id[]" value="${producto.id}">
            </td>
            <td><input type="number" name="cantidad[]" class="form-control" value="1" min="1"></td>
            <td><input type="text" name="nota_item[]" class="form-control" placeholder="Ej: sin cebolla"></td>
            <td class="text-center">
                <button type="button" class="btn btn-danger btn-sm btn-eliminar"><i class="bi bi-trash"></i></button>
            </td>
        `;
        tr.querySelector('.btn-eliminar').addEventListener('click', function () {
            tr.remove();
        });
        cuerpoTabla.appendChild(tr);
    }

    // Validación al enviar
    formPedido.addEventListener('submit', function (e) {
        if (cuerpoTabla.children.length === 0) {
            e.preventDefault();
            alert('Agregá al menos un producto al pedido.');
        }
    });
});