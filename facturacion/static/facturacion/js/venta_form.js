/* =========================================================
   Comedor A.R.M. - Formulario de nueva venta
   - Buscador de productos con AJAX
   - Buscador de cliente en vivo
   - Cálculo del total en vivo (solo visual; el total real
     lo recalcula el servidor)
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const inputProd = document.getElementById('buscar-prod');
    const resProd = document.getElementById('resultados-prod');
    const inputCliente = document.getElementById('buscar-cliente');
    const resCliente = document.getElementById('resultados-cliente');
    const selectOculto = document.getElementById('select-cliente-oculto');
    const clienteIdInput = document.getElementById('cliente-id');
    const cuerpoTabla = document.getElementById('cuerpo-tabla');
    const formVenta = document.getElementById('form-venta');

    // ------- Buscador de cliente en vivo -------
    const clientesData = [];
    for (let option of selectOculto.options) {
        clientesData.push({ id: option.value, nombre: option.text });
    }

    inputCliente.addEventListener('input', function () {
        const q = this.value.toLowerCase().trim();
        resCliente.innerHTML = '';
        clienteIdInput.value = '';
        if (q.length === 0) return;

        const filtrados = clientesData.filter(c => c.nombre.toLowerCase().includes(q));

        filtrados.forEach(c => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action';
            item.style.cursor = 'pointer';
            item.textContent = c.nombre;
            item.onclick = function (e) {
                e.preventDefault();
                inputCliente.value = c.nombre;
                clienteIdInput.value = c.id;
                resCliente.innerHTML = '';
            };
            resCliente.appendChild(item);
        });
    });

    // ------- Buscador AJAX de productos -------
    inputProd.addEventListener('input', function () {
        const query = this.value.trim();
        if (query.length < 2) {
            resProd.innerHTML = '';
            return;
        }
        fetch('/api/buscar-productos/?q=' + encodeURIComponent(query))
            .then(res => res.json())
            .then(data => {
                resProd.innerHTML = '';
                data.results.forEach(p => {
                    const item = document.createElement('a');
                    item.className = 'list-group-item list-group-item-action';
                    item.style.cursor = 'pointer';
                    item.textContent = p.nombre + ' - Gs. ' + p.precio.toLocaleString('es-PY');
                    item.onclick = function (e) {
                        e.preventDefault();
                        agregarOActualizarFila(p);
                        resProd.innerHTML = '';
                        inputProd.value = '';
                    };
                    resProd.appendChild(item);
                });
            });
    });

    function agregarOActualizarFila(producto) {
        const filasExistentes = cuerpoTabla.querySelectorAll('tr');
        let encontrado = false;

        filasExistentes.forEach(row => {
            const inputId = row.querySelector('input[name="producto_id[]"]');
            if (inputId && parseInt(inputId.value) === producto.id) {
                const inputCantidad = row.querySelector('.cantidad-input');
                inputCantidad.value = parseInt(inputCantidad.value) + 1;
                encontrado = true;
            }
        });

        if (!encontrado) {
            const tr = document.createElement('tr');
            tr.dataset.precio = producto.precio;

            tr.innerHTML = `
                <td>
                    ${producto.nombre}
                    <input type="hidden" name="producto_id[]" value="${producto.id}">
                    <input type="hidden" name="precio[]" value="${producto.precio}">
                </td>
                <td>Gs. ${parseFloat(producto.precio).toLocaleString('es-PY')}</td>
                <td>
                    <input type="number" name="cantidad[]" class="form-control cantidad-input" value="1" min="1">
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-danger btn-sm btn-eliminar">Eliminar</button>
                </td>
            `;

            tr.querySelector('.cantidad-input').addEventListener('input', recalcularTotal);
            tr.querySelector('.btn-eliminar').addEventListener('click', function () {
                tr.remove();
                recalcularTotal();
            });

            cuerpoTabla.appendChild(tr);
        }

        recalcularTotal();
    }

    function recalcularTotal() {
        let total = 0;
        document.querySelectorAll('#cuerpo-tabla tr').forEach(row => {
            const precio = parseFloat(row.dataset.precio) || 0;
            const cant = parseInt(row.querySelector('.cantidad-input').value) || 0;
            total += precio * cant;
        });
        document.getElementById('total-monto').innerText = total.toLocaleString('es-PY');
        document.getElementById('total-input').value = total;
    }

    // ------- Validación al enviar -------
    formVenta.addEventListener('submit', function (e) {
        if (!clienteIdInput.value) {
            e.preventDefault();
            alert('Por favor selecciona un cliente de la lista sugerida.');
            return;
        }
        if (cuerpoTabla.children.length === 0) {
            e.preventDefault();
            alert('Agrega al menos un producto para realizar la venta.');
            return;
        }
    });
});