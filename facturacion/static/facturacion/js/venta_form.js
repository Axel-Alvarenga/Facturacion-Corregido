/* =========================================================
   Comedor A.R.M. - Formulario de nueva venta
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
    const btnConfirmarTexto = document.getElementById('btnConfirmarTexto');

    // Modal de éxito
    const modalExitoEl = document.getElementById('modalVentaExitosa');
    const modalExitoInstance = modalExitoEl ? new bootstrap.Modal(modalExitoEl) : null;

    // Modal de ítem manual
    const modalManualEl = document.getElementById('modalItemManual');
    const modalManualInstance = modalManualEl ? new bootstrap.Modal(modalManualEl) : null;
    const btnAbrirManual = document.getElementById('btnAgregarManual');
    const btnGuardarManual = document.getElementById('btnGuardarManual');
    const inputManualDesc = document.getElementById('manual-descripcion');
    const inputManualPrecio = document.getElementById('manual-precio');

    // Modal de vaciar carrito
    const modalVaciarEl = document.getElementById('modalVaciarCarrito');
    const modalVaciarInstance = modalVaciarEl ? new bootstrap.Modal(modalVaciarEl) : null;
    const btnConfirmarVaciar = document.getElementById('btnConfirmarVaciar');

    // Select de forma de pago
    const selectFormaPago = document.getElementById('select-forma-pago');

    // Banner de aviso
    const avisoCredito = document.getElementById('aviso-credito');

    // Botón VENDER
    const btnVender = document.getElementById('btn-vender');

    // Bloque de efectivo en el modal de confirmación
    const bloqueEfectivo = document.getElementById('bloque-efectivo');
    const inputMontoPagado = document.getElementById('input-monto-pagado');
    const vueltoMonto = document.getElementById('vuelto-monto');
    const vueltoError = document.getElementById('vuelto-error');
    const vueltoPanel = document.getElementById('vuelto-panel');
    const montoPagadoHidden = document.getElementById('monto-pagado-input');

    let totalActual = 0;

    // ============================================
    // Foco inicial
    // ============================================
    setTimeout(function () { inputProd.focus(); }, 300);

    // ============================================
    // Buscador de cliente en vivo
    // ============================================
    const clientesData = [];
    for (let option of selectOculto.options) {
        clientesData.push({ id: option.value, nombre: option.text });
    }

    inputCliente.addEventListener('input', function () {
        const q = this.value.toLowerCase().trim();
        resCliente.innerHTML = '';
        clienteIdInput.value = '';
        ocultarAvisoCredito();
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
                ocultarAvisoCredito();
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
    // Enter en buscador de productos
    // ============================================
    inputProd.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;

        const texto = inputProd.value.trim();
        const items = resProd.querySelectorAll('a');
        const hayProductosEnTabla = cuerpoTabla.children.length > 0;

        if (texto.length > 0) {
            if (items.length > 0) return;
            e.preventDefault();
            return;
        }

        e.preventDefault();

        if (hayProductosEnTabla) {
            formVenta.requestSubmit();
        }
    });

    // ============================================
    // Agregar producto
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
        tr.classList.add('fila-manual');
        tr.innerHTML = `
            <td>
                <i class="bi bi-pencil-square text-warning"></i>
                ${descripcion}
                <input type="hidden" name="manual_descripcion[]" value="${descripcion}">
            </td>
            <td class="fw-bold">Gs. ${precio.toLocaleString('es-PY')}</td>
            <td>
                <span class="texto-secundario small">Ítem manual (sin cantidad)</span>
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
    // Recálculo del total
    // ============================================
    let ultimoTotal = 0;

    function recalcularTotal() {
        let total = 0;
        let cantidadItems = 0;

        document.querySelectorAll('#cuerpo-tabla tr').forEach(row => {
            const tipo = row.dataset.tipo;
            const precio = parseFloat(row.dataset.precio) || 0;
            cantidadItems += 1;

            if (tipo === 'manual') {
                total += precio;
            } else {
                const cant = parseInt(row.querySelector('.cantidad-input').value) || 0;
                total += precio * cant;
            }
        });

        totalActual = total;

        const totalTexto = 'Gs. ' + total.toLocaleString('es-PY');
        const totalEl = document.getElementById('total-monto');
        if (totalEl) totalEl.innerText = totalTexto;

        const itemsEl = document.getElementById('total-items');
        if (itemsEl) itemsEl.innerText = cantidadItems;

        const totalInput = document.getElementById('total-input');
        if (totalInput) totalInput.value = total;

        if (total !== ultimoTotal) {
            const panel = document.getElementById('total-panel');
            if (panel) {
                panel.classList.remove('total-flash');
                void panel.offsetWidth;
                panel.classList.add('total-flash');
                setTimeout(() => panel.classList.remove('total-flash'), 450);
            }
            ultimoTotal = total;
        }
    }

    // ============================================
    // Vaciar carrito
    // ============================================
    if (modalVaciarEl) {
        modalVaciarEl.addEventListener('show.bs.modal', function () {
            const cantidadItems = cuerpoTabla.children.length;
            const totalTexto = document.getElementById('total-monto').innerText;
            document.getElementById('vaciar-cantidad').textContent = cantidadItems;
            document.getElementById('vaciar-total').textContent = totalTexto;
        });

        modalVaciarEl.addEventListener('shown.bs.modal', function () {
            const btnCancelar = modalVaciarEl.querySelector('.btn-secondary');
            if (btnCancelar) btnCancelar.focus();
        });
    }

    if (btnConfirmarVaciar) {
        btnConfirmarVaciar.addEventListener('click', function () {
            cuerpoTabla.innerHTML = '';
            recalcularTotal();
            modalVaciarInstance.hide();
            inputProd.focus();
        });
    }

    // ============================================
    // Aviso de crédito sin cliente
    // ============================================
    function mostrarAvisoCredito() {
        if (avisoCredito) {
            avisoCredito.style.display = 'flex';
            avisoCredito.classList.remove('aviso-aparece');
            void avisoCredito.offsetWidth;
            avisoCredito.classList.add('aviso-aparece');
        }
        if (inputCliente) {
            inputCliente.classList.remove('shake');
            void inputCliente.offsetWidth;
            inputCliente.classList.add('shake', 'input-error');
            setTimeout(function () {
                inputCliente.classList.remove('shake');
            }, 500);
            setTimeout(function () {
                inputCliente.focus();
            }, 100);
        }
        if (avisoCredito) {
            avisoCredito.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function ocultarAvisoCredito() {
        if (avisoCredito) avisoCredito.style.display = 'none';
        if (inputCliente) inputCliente.classList.remove('input-error');
    }

    function esConsumidorFinal() {
        const nombre = inputCliente.value.trim().toLowerCase();
        return nombre === 'consumidor final';
    }

    // ============================================
    // Cálculo del vuelto
    // ============================================
    function actualizarVuelto() {
        if (!inputMontoPagado) return;

        const montoPagado = parseFloat(inputMontoPagado.value) || 0;
        const vuelto = montoPagado - totalActual;

        if (vuelto < 0) {
            // Falta plata
            vueltoMonto.textContent = 'Gs. 0';
            vueltoMonto.className = 'fs-4 fw-bold text-danger';
            vueltoPanel.classList.add('border', 'border-danger');
            if (vueltoError) vueltoError.style.display = 'block';
            if (btnConfirmar) btnConfirmar.disabled = true;
            btnConfirmar.classList.add('disabled');
        } else {
            vueltoMonto.textContent = 'Gs. ' + vuelto.toLocaleString('es-PY');
            vueltoMonto.className = 'fs-4 fw-bold text-success';
            vueltoPanel.classList.remove('border', 'border-danger');
            if (vueltoError) vueltoError.style.display = 'none';
            if (btnConfirmar) btnConfirmar.disabled = false;
            btnConfirmar.classList.remove('disabled');
        }

        // Guardar en el hidden para el POST
        if (montoPagadoHidden) {
            montoPagadoHidden.value = montoPagado > 0 ? montoPagado : '';
        }
    }

    if (inputMontoPagado) {
        inputMontoPagado.addEventListener('input', actualizarVuelto);
        inputMontoPagado.addEventListener('focus', function () {
            this.select();
        });
    }

    // ============================================
    // Submit
    // ============================================
    formVenta.addEventListener('submit', function (e) {
        e.preventDefault();

        if (cuerpoTabla.children.length === 0) {
            alert('Agregá al menos un producto o un ítem manual.');
            inputProd.focus();
            return;
        }

        const formaPago = selectFormaPago ? selectFormaPago.value : 'EFECTIVO';
        const tieneClienteReal = inputCliente.value.trim() !== '' &&
                                 clienteIdInput.value !== '' &&
                                 !esConsumidorFinal();

        if (formaPago === 'CREDITO' && !tieneClienteReal) {
            mostrarAvisoCredito();
            return;
        }

        ocultarAvisoCredito();

        const cantidadItems = cuerpoTabla.children.length;
        const totalTexto = document.getElementById('total-monto').innerText;
        const clienteTexto = inputCliente.value.trim() || 'Consumidor Final';

        document.getElementById('confirmar-cantidad').textContent = cantidadItems;
        document.getElementById('confirmar-cliente').textContent = clienteTexto;
        document.getElementById('confirmar-total').textContent = totalTexto;

        // Mostrar/ocultar bloque de efectivo
        if (formaPago === 'EFECTIVO') {
            bloqueEfectivo.style.display = 'block';
            // Inicializar con el total
            inputMontoPagado.value = totalActual;
            actualizarVuelto();
        } else {
            bloqueEfectivo.style.display = 'none';
            if (montoPagadoHidden) montoPagadoHidden.value = '';
        }

        modalInstance.show();
    });

    // ============================================
    // El botón VENDER dispara el submit
    // ============================================
    if (btnVender) {
        btnVender.addEventListener('click', function () {
            formVenta.requestSubmit();
        });
    }

    // ============================================
    // Confirmar venta (AJAX)
    // ============================================
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function () {
            enviarVentaAjax();
        });
    }

    function enviarVentaAjax() {
        btnConfirmar.disabled = true;
        if (btnConfirmarTexto) btnConfirmarTexto.textContent = 'Procesando...';
        btnConfirmar.classList.add('disabled');

        const formData = new FormData(formVenta);

        fetch(formVenta.action || window.location.href, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
            credentials: 'same-origin',
        })
        .then(async (res) => {
            const data = await res.json();
            return { ok: res.ok, data };
        })
        .then(({ ok, data }) => {
            if (ok && data.ok) {
                modalInstance.hide();
                mostrarModalExito(data.venta);
            } else {
                alert('Error: ' + (data.error || 'No se pudo registrar la venta.'));
                restaurarBotonConfirmar();
            }
        })
        .catch((err) => {
            console.error(err);
            alert('Error de conexión. Revisá tu red e intentá de nuevo.');
            restaurarBotonConfirmar();
        });
    }

    function restaurarBotonConfirmar() {
        btnConfirmar.disabled = false;
        if (btnConfirmarTexto) btnConfirmarTexto.textContent = 'Sí, vender';
        btnConfirmar.classList.remove('disabled');
    }

    // ============================================
    // Modal de éxito
    // ============================================
    function mostrarModalExito(venta) {
        document.getElementById('exito-venta-id').textContent = '#' + venta.id;
        document.getElementById('exito-total').textContent = 'Gs. ' + venta.total_fmt;
        document.getElementById('exito-cliente').textContent = venta.cliente;
        document.getElementById('exito-forma-pago').textContent = venta.forma_pago;
        document.getElementById('exito-fecha').textContent = venta.fecha;
        document.getElementById('btn-imprimir-ticket').href = venta.ticket_url;

        // Aviso de transferencia pendiente
        const avisoPendiente = document.getElementById('exito-aviso-pendiente');
        if (avisoPendiente) {
            avisoPendiente.style.display = venta.es_pendiente ? 'block' : 'none';
        }

        // Bloque de vuelto
        const exitoVuelto = document.getElementById('exito-vuelto');
        if (exitoVuelto) {
            if (venta.tiene_vuelto) {
                document.getElementById('exito-monto-pagado').textContent =
                    'Gs. ' + venta.monto_pagado_fmt;
                document.getElementById('exito-vuelto-monto').textContent =
                    'Gs. ' + venta.vuelto_fmt;
                exitoVuelto.style.display = 'block';
            } else {
                exitoVuelto.style.display = 'none';
            }
        }

        // Limpiar formulario
        cuerpoTabla.innerHTML = '';
        inputCliente.value = '';
        clienteIdInput.value = '';
        inputProd.value = '';
        selectFormaPago.value = 'EFECTIVO';
        if (montoPagadoHidden) montoPagadoHidden.value = '';
        recalcularTotal();

        restaurarBotonConfirmar();

        setTimeout(function () {
            modalExitoInstance.show();
        }, 250);
    }

    // ============================================
    // Botón "Nueva venta" del modal de éxito
    // ============================================
    const btnNuevaVentaModal = document.getElementById('btn-nueva-venta-modal');
    if (btnNuevaVentaModal) {
        btnNuevaVentaModal.addEventListener('click', function () {
            modalExitoInstance.hide();
            setTimeout(function () {
                inputProd.focus();
            }, 300);
        });
    }

    // ============================================
    // Enter en el modal de confirmación
    // ============================================
    if (modalEl) {
        modalEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !btnConfirmar.disabled) {
                e.preventDefault();
                btnConfirmar.click();
            }
        });

        modalEl.addEventListener('shown.bs.modal', function () {
            // Si es efectivo, hacer foco en el input del monto pagado
            const formaPago = selectFormaPago ? selectFormaPago.value : 'EFECTIVO';
            if (formaPago === 'EFECTIVO' && inputMontoPagado) {
                inputMontoPagado.focus();
                inputMontoPagado.select();
            } else {
                btnConfirmar.focus();
            }
        });
    }

    if (modalExitoEl) {
        modalExitoEl.addEventListener('shown.bs.modal', function () {
            const btnNueva = document.getElementById('btn-nueva-venta-modal');
            if (btnNueva) btnNueva.focus();
        });
    }
});