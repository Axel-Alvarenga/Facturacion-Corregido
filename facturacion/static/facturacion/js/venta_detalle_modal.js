/* =========================================================
   Comedor A.R.M. - Modal de Detalle de Venta (informe)
   - Escucha clics en filas [data-venta-id]
   - Hace fetch() a venta_detalle_api
   - Llena el modal y lo muestra
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalDetalleVenta');
    if (!modalEl) return;

    const modalBody  = modalEl.querySelector('.modal-body');
    const modalTitle = modalEl.querySelector('.modal-title');
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);

    // URLs globales (inyectadas por config_global.js desde #arm-config-urls)
    const urls = window.__ARM_URLS__ || {};
    const urlTemplate = urls.venta_detalle_api || null;

    if (!urlTemplate) {
        console.warn('[venta_detalle_modal] Falta venta_detalle_api en #arm-config-urls');
        return;
    }

    function urlDetalle(ventaId) {
        // La URL llega como /ventas/0/detalle/ → reemplazamos el 0 por el id real
        return urlTemplate.replace(/\/0\/detalle\/?$/, `/${ventaId}/detalle/`);
    }

    function esc(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderDetalle(v) {
        const badgeEstado = v.estado_raw === 'PENDIENTE'
            ? `<span class="badge bg-warning text-dark">${esc(v.estado)}</span>`
            : `<span class="badge bg-success">${esc(v.estado)}</span>`;

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
                    <div>${badgeEstado}</div>
                </div>
            </div>
        `;

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
                <span class="fw-bold fs-4" style="color:#4CAF50;">Gs. ${esc(v.total_fmt)}</span>
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
    });
});