/* =========================================================
   Comedor A.R.M. - Formulario de nueva venta
   - Buscador AJAX de productos
   - Buscador de cliente (opcional)
   - Ítems manuales (recargos, propinas, etc.)
   - Confirmación visual antes de vender
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

    // Modal de confirmación
    const modalEl = document.getElementById('modalConfirmarVenta');
    const modalInstance = modalEl ? new bootstrap.Modal(modalEl) : null;
    const btnConfirmar = document.getElementById('btnConfirmarVenta');

    // Modal de ítem manual
    const modalManualEl = document.getElementById('modalItemManual');
    const modalManualInstance = modalManualEl ? new bootstrap.Modal(modalManualEl) : null;
    const btnAbrirManual = document.getElementById('btnAgregarManual');
    const btnGuardarManual = document.getElementById('btnGuardarManual');
    const inputManualDesc = document.getElementById('manual-descripcion');
    const inputManualPrecio = document.getElementById('manual-precio');

    // ============================================
    // Foco inicial
    // ============================================
    setTimeout(function () { inputProd.focus(); }, 300);

    // ============================================
    // Buscador de cliente en vivo (opcional)
    // ============================================
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

    // ============================================
    // Buscador AJAX de productos
    // ============================================
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
                        inputProd.focus();
                    };
                    resProd.appendChild(item);
                });
            });
    });

    // ============================================
    // Agregar producto del catálogo
    // ============================================
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
            tr.dataset.tipo = 'producto';

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
                    <button type="button" class="btn btn-danger btn-sm btn-eliminar" tabindex="-1">Eliminar</button>
                </td>
            `;

            tr.querySelector('.cantidad-input').addEventListener('input', recalcularTotal);
            tr.querySelector('.btn-eliminar').addEventListener('click', function () {
                tr.remove();
                recalcularTotal();
                inputProd.focus();
            });

            cuerpoTabla.appendChild(tr);
        }

        recalcularTotal();
    }

    // ============================================
    // Ítems manuales
    // ============================================
    if (btnAbrirManual) {
        btnAbrirManual.addEventListener('click', function () {
            inputManualDesc.value = '';
            inputManualPrecio.value = '';
            modalManualInstance.show();
        });
    }

    if (modalManualEl) {
        modalManualEl.addEventListener('shown.bs.modal', function () {
            inputManualDesc.focus();
        });

        // Enter en descripción -> ir a precio; Enter en precio -> guardar
        inputManualDesc.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                inputManualPrecio.focus();
            }
        });
        inputManualPrecio.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnGuardarManual.click();
            }
        });
    }

    if (btnGuardarManual) {
        btnGuardarManual.addEventListener('click', function () {
            const desc = inputManualDesc.value.trim();
            const precio = parseFloat(inputManualPrecio.value);

            if (!desc) {
                alert('Escribí una descripción (ej: "Recargo de pan").');
                inputManualDesc.focus();
                return;
            }
            if (isNaN(precio) || precio < 0) {
                alert('Ingresá un precio válido (mayor o igual a 0).');
                inputManualPrecio.focus();
                return;
            }

            agregarFilaManual(desc, precio);
            modalManualInstance.hide();
            inputProd.focus();
        });
    }

    function agregarFilaManual(descripcion, precio) {
        const tr = document.createElement('tr');
        tr.dataset.precio = precio;
        tr.dataset.tipo = 'manual';
        // Estilo diferente para distinguirlo
        tr.classList.add('fila-manual');
        // No se envía "cantidad", el precio ya es total del ítem
        tr.innerHTML = `
            <td>
                <i class="bi bi-pencil-square text-warning"></i>
                ${descripcion}
                <input type="hidden" name="manual_descripcion[]" value="${descripcion}">
            </td>
            <td class="fw-bold">Gs. ${precio.toLocaleString('es-PY')}</td>
            <td>
                <span class="text-muted small">Ítem manual (sin cantidad)</span>
                <input type="hidden" name="manual_precio[]" value="${precio}">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-danger btn-sm btn-eliminar-manual" tabindex="-1">Eliminar</button>
            </td>
        `;

        tr.querySelector('.btn-eliminar-manual').addEventListener('click', function () {
            tr.remove();
            recalcularTotal();
            inputProd.focus();
        });

        cuerpoTabla.appendChild(tr);
        recalcularTotal();
    }

    // ============================================
    // Recálculo del total (incluye productos + manuales)
    // ============================================
    function recalcularTotal() {
        let total = 0;
        document.querySelectorAll('#cuerpo-tabla tr').forEach(row => {
            const tipo = row.dataset.tipo;
            const precio = parseFloat(row.dataset.precio) || 0;

            if (tipo === 'manual') {
                total += precio;
            } else {
                const cant = parseInt(row.querySelector('.cantidad-input').value) || 0;
                total += precio * cant;
            }
        });
        document.getElementById('total-monto').innerText = total.toLocaleString('es-PY');
        document.getElementById('total-input').value = total;
    }

    // ============================================
    // Submit: abre el modal de confirmación
    // ============================================
    formVenta.addEventListener('submit', function (e) {
        e.preventDefault();

        if (cuerpoTabla.children.length === 0) {
            alert('Agregá al menos un producto o un ítem manual.');
            inputProd.focus();
            return;
        }

        const cantidadItems = cuerpoTabla.children.length;
        const totalTexto = document.getElementById('total-monto').innerText;
        const clienteTexto = inputCliente.value.trim() || 'Consumidor Final';

        document.getElementById('confirmar-cantidad').textContent = cantidadItems;
        document.getElementById('confirmar-cliente').textContent = clienteTexto;
        document.getElementById('confirmar-total').textContent = 'Gs. ' + totalTexto;

        modalInstance.show();
    });

    // ============================================
    // Confirmar venta desde el modal
    // ============================================
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function () {
            modalInstance.hide();
            formVenta.submit();
        });
    }

    if (modalEl) {
        modalEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnConfirmar.click();
            }
        });

        modalEl.addEventListener('shown.bs.modal', function () {
            btnConfirmar.focus();
        });
    }
});