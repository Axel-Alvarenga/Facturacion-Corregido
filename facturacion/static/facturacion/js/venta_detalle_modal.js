/* =========================================================
   Comedor A.R.M. - Modal de Detalle de Venta (informe)
   - Escucha clics en filas [data-venta-id]
   - Hace fetch() a venta_detalle_api
   - Llena el modal y lo muestra
   - Botón "Anular venta" (solo superusuarios)
   - Botón "Confirmar transferencia" (si está pendiente)
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalDetalleVenta');
    if (!modalEl) return;

    const modalBody  = modalEl.querySelector('.modal-body');
    const modalTitle = modalEl.querySelector('.modal-title');
    const modalFooter = modalEl.querySelector('.modal-footer');
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);

    const urls = window.__ARM_URLS__ || {};
    const urlTemplate = urls.venta_detalle_api || null;
    const urlAnularTemplate = urls.anular_venta || null;

    if (!urlTemplate) {
        console.warn('[venta_detalle_modal] Falta venta_detalle_api en #arm-config-urls');
        return;
    }

    let ventaActualId = null;
    let ventaActualData = null;

    function urlDetalle(ventaId) {
        return urlTemplate.replace(/\/0\/detalle\/?$/, `/${ventaId}/detalle/`);
    }

    function urlAnular(ventaId) {
        if (!urlAnularTemplate) return null;
        return urlAnularTemplate.replace(/\/0\/anular\/?$/, `/${ventaId}/anular/`);
    }

    function esc(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderDetalle(v) {
        ventaActualId = v.id;
        ventaActualData = v;

        const badgeEstado = v.estado_raw === 'PENDIENTE'
            ? `<span class="badge bg-warning text-dark">${esc(v.estado)}</span>`
            : `<span class="badge bg-success">${esc(v.estado)}</span>`;

        const badgeAnulada = v.anulada
            ? `<span class="badge bg-danger ms-2">ANULADA</span>`
            : '';

        let html = `
            <div class="row g-2 mb-3">
                <div class="col-sm-6">
                    <div class="kpi-label">Cliente</div>
                    <div class="fw-bold">${esc(v.cliente)}</div>
                    ${v.nombre_local ? `<div class="texto-secundario small">${esc(v.nombre_local)}</div>` : ''}
                </div>
                <div class="col-sm-6 text-sm-end">
                    <div class="kpi-label">Fecha</div>
                    <div class="fw-bold">${esc(v.fecha)}</div>
                </div>
                <div class="col-sm-6">
                    <div class="kpi-label">Forma de pago</div>
                    <div class="fw-bold">${esc(v.forma_pago)}</div>
                </div>
                <div class="col-sm-6 text-sm-end">
                    <div class="kpi-label">Estado</div>
                    <div>${badgeEstado}${badgeAnulada}</div>
                </div>
            </div>
        `;

        if (v.anulada) {
            html += `
                <div class="alert alert-danger mb-3">
                    <i class="bi bi-x-octagon-fill"></i>
                    <strong>Venta anulada</strong>
                    ${v.fecha_anulacion ? `<div class="small mt-1">Fecha: ${esc(v.fecha_anulacion)}</div>` : ''}
                    ${v.anulada_por ? `<div class="small">Por: ${esc(v.anulada_por)}</div>` : ''}
                    ${v.motivo_anulacion ? `<div class="small">Motivo: ${esc(v.motivo_anulacion)}</div>` : ''}
                </div>
            `;
        }

        const hayProductos = Array.isArray(v.detalles) && v.detalles.length > 0;
        const hayManuales  = Array.isArray(v.items_manuales) && v.items_manuales.length > 0;

        if (hayProductos || hayManuales) {
            html += `
                <div class="tabla-local">
                  <div class="table-responsive">
                    <table class="table table-sm align-middle mb-0">
                        <thead>
                            <tr>
                                <th>Ítem</th>
                                <th class="text-center">Cant.</th>
                                <th class="text-end">Precio</th>
                                <th class="text-end">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            (v.detalles || []).forEach(d => {
                html += `
                    <tr>
                        <td>${esc(d.producto)}</td>
                        <td class="text-center">${d.cantidad}</td>
                        <td class="text-end">Gs. ${esc(d.precio_unitario_fmt)}</td>
                        <td class="text-end">Gs. ${esc(d.subtotal_fmt)}</td>
                    </tr>
                `;
            });

            (v.items_manuales || []).forEach(m => {
                html += `
                    <tr class="fila-manual">
                        <td>
                            ${esc(m.descripcion)}
                            <span class="badge bg-secondary ms-1">manual</span>
                        </td>
                        <td class="text-center">1</td>
                        <td class="text-end">Gs. ${esc(m.precio_fmt)}</td>
                        <td class="text-end">Gs. ${esc(m.precio_fmt)}</td>
                    </tr>
                `;
            });

            html += `</tbody></table></div></div>`;
        } else {
            html += `<div class="alert alert-secondary mb-0">Esta venta no tiene ítems registrados.</div>`;
        }

        html += `
            <hr>
            <div class="d-flex justify-content-between align-items-center">
                <span class="fw-bold">TOTAL</span>
                <span class="fw-bold fs-4 text-cobrado">Gs. ${esc(v.total_fmt)}</span>
            </div>
        `;

        if (v.forma_pago_raw === 'EFECTIVO' && v.monto_pagado_fmt !== null) {
            html += `
                <div class="d-flex justify-content-between texto-secundario small mt-1">
                    <span>Monto pagado</span>
                    <span>Gs. ${esc(v.monto_pagado_fmt)}</span>
                </div>
            `;
            if (v.tiene_vuelto) {
                html += `
                    <div class="d-flex justify-content-between texto-secundario small">
                        <span>Vuelto</span>
                        <span>Gs. ${esc(v.vuelto_fmt)}</span>
                    </div>
                `;
            }
        }

        modalBody.innerHTML = html;
        renderFooter(v);
    }

    function renderFooter(v) {
        const esSuper = modalEl.dataset.esSuperuser === '1';

        let html = '';

        // Botón "Confirmar transferencia" (si está pendiente)
        if (v.forma_pago_raw === 'TRANSFERENCIA' && v.estado_raw === 'PENDIENTE' && !v.anulada) {
            html += `
                <button type="button" class="btn btn-success fw-bold me-2"
                        id="btnConfirmarTransferenciaDetalle"
                        data-venta-id="${v.id}">
                    <i class="bi bi-check-circle"></i> Confirmar transferencia
                </button>
            `;
        }

        // Botón "Anular venta" (solo superusuarios)
        if (esSuper && v.puede_anularse && !v.anulada) {
            html += `
                <button type="button" class="btn btn-danger fw-bold me-auto"
                        id="btnAnularVenta"
                        data-venta-id="${v.id}">
                    <i class="bi bi-x-octagon"></i> Anular venta
                </button>
            `;
        } else if (esSuper && v.anulada) {
            html += `
                <span class="texto-secundario small me-auto">
                    <i class="bi bi-info-circle"></i> Esta venta ya fue anulada
                </span>
            `;
        } else if (esSuper && !v.puede_anularse && v.motivo_no_anulable) {
            html += `
                <span class="texto-secundario small me-auto" title="${esc(v.motivo_no_anulable)}">
                    <i class="bi bi-lock"></i> No anulable: ${esc(v.motivo_no_anulable)}
                </span>
            `;
        }

        html += `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
        `;

        modalFooter.innerHTML = html;

        // Listener del botón "Anular venta"
        const btnAnular = modalFooter.querySelector('#btnAnularVenta');
        if (btnAnular) {
            btnAnular.addEventListener('click', function () {
                abrirModalAnulacion(v);
            });
        }

        // Listener del botón "Confirmar transferencia"
        const btnConfirmar = modalFooter.querySelector('#btnConfirmarTransferenciaDetalle');
        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', function () {
                abrirModalConfirmarTransferencia(v);
            });
        }
    }

    async function abrirDetalle(ventaId) {
        if (!ventaId) return;

        modalTitle.innerHTML = `<i class="bi bi-receipt text-warning"></i> Venta #${esc(ventaId)}`;
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-warning" role="status"></div>
                <div class="texto-secundario small mt-2">Cargando detalle…</div>
            </div>
        `;
        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
        `;
        modalInstance.show();

        try {
            const resp = await fetch(urlDetalle(ventaId), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            if (!data.ok || !data.venta) throw new Error('Respuesta inválida');
            renderDetalle(data.venta);
        } catch (err) {
            console.error('[venta_detalle_modal] Error:', err);
            modalBody.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-x-circle"></i>
                    No se pudo cargar el detalle de la venta.
                    <div class="small mt-1">${esc(err.message || 'Error desconocido')}</div>
                </div>
            `;
        }
    }

    // ============================================================
    // Modal de confirmación de transferencia (desde el detalle)
    // ============================================================
    function abrirModalConfirmarTransferencia(venta) {
        modalInstance.hide();

        const modalConf = document.getElementById('modalConfirmarTransferencia');
        if (!modalConf) {
            alert('Falta el modal #modalConfirmarTransferencia en el template.');
            return;
        }

        document.getElementById('conf-transf-venta-id').textContent = '#' + venta.id;
        document.getElementById('conf-transf-cliente').textContent = venta.cliente;
        document.getElementById('conf-transf-monto').textContent = 'Gs. ' + venta.total_fmt;

        const form = document.getElementById('formConfirmarTransferencia');
        form.action = '/ventas/' + venta.id + '/confirmar-transferencia/';

        const modal = bootstrap.Modal.getOrCreateInstance(modalConf);
        modal.show();
    }

    // ============================================================
    // Modal de confirmación de anulación
    // ============================================================
    function abrirModalAnulacion(venta) {
        modalInstance.hide();

        const modalAnularEl = document.getElementById('modalAnularVenta');
        if (!modalAnularEl) {
            alert('Falta el modal #modalAnularVenta en el template.');
            return;
        }

        document.getElementById('anular-venta-id').textContent = '#' + venta.id;
        document.getElementById('anular-venta-cliente').textContent = venta.cliente;
        document.getElementById('anular-venta-total').textContent = 'Gs. ' + venta.total_fmt;
        document.getElementById('anular-venta-forma-pago').textContent = venta.forma_pago;

        const form = document.getElementById('formAnularVenta');
        const motivoInput = document.getElementById('anular-motivo');
        const errorDiv = document.getElementById('anular-error');
        const btnConfirmar = document.getElementById('btnConfirmarAnulacion');

        motivoInput.value = '';
        errorDiv.style.display = 'none';
        btnConfirmar.disabled = false;
        btnConfirmar.innerHTML = '<i class="bi bi-x-octagon"></i> Sí, anular venta';

        const urlAnularFinal = urlAnular(venta.id);
        form.action = urlAnularFinal;

        form.onsubmit = function (e) {
            e.preventDefault();

            const motivo = motivoInput.value.trim();
            if (!motivo) {
                errorDiv.textContent = 'Tenés que indicar el motivo de la anulación.';
                errorDiv.style.display = 'block';
                motivoInput.focus();
                return;
            }

            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Anulando...';

            const formData = new FormData(form);

            fetch(urlAnularFinal, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            })
            .then(async (res) => {
                if (res.redirected) {
                    window.location.href = res.url;
                    return null;
                }
                const text = await res.text();
                try {
                    return JSON.parse(text);
                } catch {
                    return { ok: false, error: 'Respuesta inesperada del servidor.' };
                }
            })
            .then((data) => {
                if (data === null) return;
                if (data && data.ok) {
                    window.location.href = '/informes/ventas/';
                } else {
                    errorDiv.textContent = (data && data.error) || 'No se pudo anular la venta.';
                    errorDiv.style.display = 'block';
                    btnConfirmar.disabled = false;
                    btnConfirmar.innerHTML = '<i class="bi bi-x-octagon"></i> Sí, anular venta';
                }
            })
            .catch((err) => {
                console.error(err);
                errorDiv.textContent = 'Error de conexión. Revisá tu red e intentá de nuevo.';
                errorDiv.style.display = 'block';
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = '<i class="bi bi-x-octagon"></i> Sí, anular venta';
            });
        };

        const modalAnular = bootstrap.Modal.getOrCreateInstance(modalAnularEl);
        modalAnular.show();

        modalAnularEl.addEventListener('shown.bs.modal', function () {
            motivoInput.focus();
        }, { once: true });
    }

    // Delegación: cualquier clic en <tr data-venta-id>
    document.addEventListener('click', function (ev) {
        const fila = ev.target.closest('tr[data-venta-id]');
        if (!fila) return;
        if (ev.target.closest('a, button, input, select, textarea')) return;
        ev.preventDefault();
        abrirDetalle(fila.getAttribute('data-venta-id'));
    });

    // Limpiar al cerrar
    modalEl.addEventListener('hidden.bs.modal', function () {
        modalBody.innerHTML = '';
        ventaActualId = null;
        ventaActualData = null;
    });
});