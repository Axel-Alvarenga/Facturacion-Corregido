/* =========================================================
   Comedor A.R.M. - Historial de Ventas por Cliente
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalHistorialVentas');
    if (!modalEl) return;

    const modalBody = document.getElementById('historial-modal-body');
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);

    function esc(str) {
        if (str === null || str === undefined) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    modalEl.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        if (!boton) return;

        const clienteId = boton.getAttribute('data-id');
        
        // Mostrar spinner
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-warning" role="status"></div>
                <div class="texto-secundario small mt-2">Cargando historial…</div>
            </div>
        `;

        // Hacer fetch al endpoint
        fetch('/clientes/' + clienteId + '/historial/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin',
        })
        .then(res => res.json())
        .then(data => {
            if (!data.ok) throw new Error('Error al cargar');

            let html = `
                <div class="alert alert-secondary mb-3">
                    <strong>Cliente:</strong> ${esc(data.cliente.nombre)} (${esc(data.cliente.nombre_local)})<br>
                    <strong>Deuda actual:</strong> Gs. ${esc(data.cliente.deuda_fmt)}
                </div>
            `;

            if (data.ventas.length === 0) {
                html += `<div class="alert alert-info mb-0">Este cliente no tiene ventas registradas.</div>`;
            } else {
                html += `
                    <div class="tabla-local">
                      <div class="table-responsive">
                        <table class="table table-sm align-middle mb-0">
                            <thead>
                                <tr>
                                    <th># Venta</th>
                                    <th>Fecha</th>
                                    <th>Productos / Detalle</th>
                                    <th>Forma de Pago</th>
                                    <th>Estado</th>
                                    <th class="text-end">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                data.ventas.forEach(v => {
                    const badgeEstado = v.estado_raw === 'PENDIENTE' 
                        ? '<span class="badge bg-warning text-dark">Pendiente</span>' 
                        : '<span class="badge bg-success">Confirmada</span>';
                        
                    const badgeAnulada = v.anulada ? '<span class="badge bg-danger ms-1">ANULADA</span>' : '';

                    html += `
                        <tr class="${v.anulada ? 'opacity-50' : ''}">
                            <td>${v.id} ${badgeAnulada}</td>
                            <td class="small">${esc(v.fecha)}</td>
                            <td class="small">${esc(v.productos)}</td>
                            <td>${esc(v.forma_pago)}</td>
                            <td>${badgeEstado}</td>
                            <td class="fw-bold text-end">Gs. ${esc(v.total_fmt)}</td>
                        </tr>
                    `;
                });

                html += `</tbody></table></div></div>`;
            }

            modalBody.innerHTML = html;
        })
        .catch(err => {
            console.error(err);
            modalBody.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-x-circle"></i> No se pudo cargar el historial.
                </div>
            `;
        });
    });
});