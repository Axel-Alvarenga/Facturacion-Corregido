/* =========================================================
   Comedor A.R.M. - Informe de ventas
   - Modal de confirmación de transferencia (individual)
   - Modal de transferencias pendientes (lista)
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const urls = window.__ARM_URLS__ || {};
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

    // ============================================================
    // Modal: Confirmar transferencia (individual)
    // ============================================================
    const modalConfTransf = document.getElementById('modalConfirmarTransferencia');
    if (modalConfTransf) {
        modalConfTransf.addEventListener('show.bs.modal', function (event) {
            const boton = event.relatedTarget;
            if (!boton) return;

            const ventaId = boton.getAttribute('data-venta-id');
            const ventaTotal = boton.getAttribute('data-venta-total');
            const ventaCliente = boton.getAttribute('data-venta-cliente');

            document.getElementById('conf-transf-venta-id').textContent = '#' + ventaId;
            document.getElementById('conf-transf-cliente').textContent = ventaCliente;
            document.getElementById('conf-transf-monto').textContent = ventaTotal;

            const form = document.getElementById('formConfirmarTransferencia');
            form.action = '/ventas/' + ventaId + '/confirmar-transferencia/';
        });
    }

    // ============================================================
    // Modal: Transferencias pendientes (lista)
    // ============================================================
    const modalPendientes = document.getElementById('modalTransferenciasPendientes');
    if (!modalPendientes) return;

    const bodyPendientes = document.getElementById('transferencias-pendientes-body');

    function esc(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async function cargarPendientes() {
        bodyPendientes.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-warning" role="status"></div>
                <div class="texto-secundario small mt-2">Cargando transferencias pendientes…</div>
            </div>
        `;

        try {
            const resp = await fetch(urls.transferencias_pendientes_api, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            });
            const data = await resp.json();
            if (!data.ok) throw new Error('Error al cargar transferencias');

            if (data.ventas.length === 0) {
                bodyPendientes.innerHTML = `
                    <div class="alert alert-success mb-0">
                        <i class="bi bi-check-circle-fill"></i>
                        No hay transferencias pendientes. Todo confirmado. 🎉
                    </div>
                `;
                return;
            }

            let html = `
                <p class="texto-secundario small mb-3">
                    <i class="bi bi-info-circle"></i>
                    Confirmá solo las transferencias que ya recibiste. Las que no
                    confirmes seguirán pendientes.
                </p>
                <div class="tabla-local">
                  <div class="table-responsive">
                    <table class="table table-sm align-middle mb-0">
                        <thead>
                            <tr>
                                <th>Venta</th>
                                <th>Cliente</th>
                                <th>Fecha</th>
                                <th class="text-end">Monto</th>
                                <th class="text-center">Acción</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.ventas.forEach(v => {
                const nombreConLocal = v.nombre_local
                    ? `${v.cliente} (${v.nombre_local})`
                    : v.cliente;

                html += `
                    <tr data-venta-pendiente-id="${v.id}">
                        <td><strong>#${v.id}</strong></td>
                        <td>${esc(nombreConLocal)}</td>
                        <td class="small">${esc(v.fecha)}</td>
                        <td class="text-end fw-bold">Gs. ${esc(v.total_fmt)}</td>
                        <td class="text-center">
                            <button type="button"
                                    class="btn btn-success btn-sm fw-bold btn-confirmar-pendiente"
                                    data-venta-id="${v.id}"
                                    data-confirmar-url="${esc(v.confirmar_url)}">
                                <i class="bi bi-check-circle"></i> Confirmar
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table></div></div>`;
            bodyPendientes.innerHTML = html;

            bodyPendientes.querySelectorAll('.btn-confirmar-pendiente').forEach(btn => {
                btn.addEventListener('click', async function () {
                    const url = this.getAttribute('data-confirmar-url');

                    this.disabled = true;
                    this.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

                    try {
                        const formData = new FormData();
                        formData.append('csrfmiddlewaretoken', csrfToken);

                        const resp = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest',
                            },
                            body: formData,
                            credentials: 'same-origin',
                        });

                        if (resp.redirected || resp.ok) {
                            const fila = this.closest('tr');
                            fila.remove();

                            const restantes = bodyPendientes.querySelectorAll('tr[data-venta-pendiente-id]').length;
                            if (restantes === 0) {
                                bodyPendientes.innerHTML = `
                                    <div class="alert alert-success mb-0">
                                        <i class="bi bi-check-circle-fill"></i>
                                        ¡Todas las transferencias fueron confirmadas! 🎉
                                    </div>
                                `;
                                setTimeout(() => window.location.reload(), 1500);
                            } else {
                                setTimeout(() => window.location.reload(), 1000);
                            }
                        } else {
                            throw new Error('Error al confirmar');
                        }
                    } catch (err) {
                        console.error(err);
                        this.disabled = false;
                        this.innerHTML = '<i class="bi bi-check-circle"></i> Confirmar';
                        alert('No se pudo confirmar la transferencia. Recargá la página e intentá de nuevo.');
                    }
                });
            });

        } catch (err) {
            console.error(err);
            bodyPendientes.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-x-circle"></i> No se pudieron cargar las transferencias pendientes.
                </div>
            `;
        }
    }

    modalPendientes.addEventListener('show.bs.modal', function () {
        cargarPendientes();
    });
});