/* =========================================================
   Comedor A.R.M. - Modal de Caja
   - Estado actual (abierta / cerrada)
   - Abrir caja
   - Cerrar caja
   - Ingreso / retiro manual
   - Actualización de la tarjeta del dashboard
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalCajaEl = document.getElementById('modalCaja');
    if (!modalCajaEl) return;

    const urls = window.__ARM_URLS__ || {};
    const csrfToken = (window.__ARM_CIERRE_CONFIG__ || {}).csrfToken || '';

    const modalCaja = bootstrap.Modal.getOrCreateInstance(modalCajaEl);
    const modalAbrirEl = document.getElementById('modalAbrirCaja');
    const modalCerrarEl = document.getElementById('modalCerrarCaja');
    const modalMovimientoEl = document.getElementById('modalMovimientoCaja');

    const modalAbrir = modalAbrirEl ? bootstrap.Modal.getOrCreateInstance(modalAbrirEl) : null;
    const modalCerrar = modalCerrarEl ? bootstrap.Modal.getOrCreateInstance(modalCerrarEl) : null;
    const modalMovimiento = modalMovimientoEl ? bootstrap.Modal.getOrCreateInstance(modalMovimientoEl) : null;

    const modalBody = document.getElementById('caja-modal-body');
    const modalFooter = document.getElementById('caja-modal-footer');
    const badgeNav = document.getElementById('badge-caja-estado');

    let cajaActual = null;

    // ============================================================
    // Utilidades
    // ============================================================
    function esc(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function fmtGs(valor) {
        if (valor === null || valor === undefined) return 'Gs. 0';
        return 'Gs. ' + Math.round(valor).toLocaleString('es-PY');
    }

    async function fetchJSON(url, options = {}) {
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            ...(options.headers || {}),
        };
        if (options.method === 'POST') {
            headers['X-CSRFToken'] = csrfToken;
        }
        const resp = await fetch(url, {
            credentials: 'same-origin',
            ...options,
            headers,
        });
        const data = await resp.json();
        return { ok: resp.ok, data };
    }

    // ============================================================
    // Badge del navbar
    // ============================================================
    function actualizarBadge(caja) {
        if (!badgeNav) return;
        if (caja && caja.estado === 'ABIERTA') {
            badgeNav.className = 'badge bg-success';
            badgeNav.textContent = 'Abierta';
            badgeNav.style.display = 'inline-block';
        } else {
            badgeNav.className = 'badge bg-secondary';
            badgeNav.textContent = 'Cerrada';
            badgeNav.style.display = 'inline-block';
        }
    }

    // ============================================================
    // Tarjeta del dashboard (si existe en la página actual)
    // ============================================================
    function actualizarTarjetaDashboard(caja) {
        const tarjeta = document.getElementById('dashboard-caja-card');
        if (!tarjeta) return;

        const estadoEl = tarjeta.querySelector('[data-caja-estado]');
        const esperadoEl = tarjeta.querySelector('[data-caja-esperado]');
        const labelEsperado = tarjeta.querySelector('.texto-secundario.small');
        const movsEl = tarjeta.querySelector('[data-caja-movs]');

        if (caja && caja.estado === 'ABIERTA') {
            if (estadoEl) estadoEl.innerHTML = '<span class="badge bg-success">Abierta</span>';
            if (labelEsperado) labelEsperado.textContent = 'Esperado';
            if (esperadoEl) esperadoEl.textContent = caja.totales.esperado_fmt;
            if (movsEl) {
                const activos = (caja.movimientos || []).filter(m => !m.anulado).length;
                movsEl.textContent = activos;
            }
        } else {
            if (estadoEl) estadoEl.innerHTML = '<span class="badge bg-secondary">Cerrada</span>';
            if (labelEsperado) labelEsperado.textContent = 'Último cierre';
            if (esperadoEl) {
                esperadoEl.textContent = (caja && caja.monto_cierre_real_fmt)
                    ? caja.monto_cierre_real_fmt
                    : 'Gs. 0';
            }
            if (movsEl) movsEl.textContent = '0';
        }
    }

    // ============================================================
    // Cargar estado actual y renderizar
    // ============================================================
    async function cargarEstado() {
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-warning" role="status"></div>
                <div class="texto-secundario small mt-2">Cargando estado de caja…</div>
            </div>
        `;
        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
        `;

        try {
            const { ok, data } = await fetchJSON(urls.caja_actual_api);
            if (!ok || !data.ok) throw new Error(data.error || 'Error al cargar caja');

            cajaActual = data.caja;
            actualizarBadge(cajaActual);
            actualizarTarjetaDashboard(cajaActual);

            if (data.hay_caja_abierta) {
                renderCajaAbierta(data.caja);
            } else if (data.caja) {
                renderCajaCerrada(data.caja);
            } else {
                renderSinCaja();
            }
        } catch (err) {
            console.error(err);
            modalBody.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-x-circle"></i> No se pudo cargar el estado de caja.
                    <div class="small mt-1">${esc(err.message)}</div>
                </div>
            `;
        }
    }

    // ============================================================
    // Render: sin caja
    // ============================================================
    function renderSinCaja() {
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-safe" style="font-size: 3rem; color: var(--color-texto-muted);"></i>
                <p class="mt-3 mb-1">No hay caja abierta.</p>
                <p class="texto-secundario small">Abrí una caja para empezar a registrar movimientos.</p>
            </div>
        `;
        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
            <button type="button" class="btn btn-success fw-bold" id="btnAbrirCajaDesdeModal">
                <i class="bi bi-unlock"></i> Abrir caja
            </button>
        `;
        document.getElementById('btnAbrirCajaDesdeModal').addEventListener('click', function () {
            modalCaja.hide();
            abrirModalAbrir();
        });
    }

    // ============================================================
    // Render: caja abierta
    // ============================================================
    function renderCajaAbierta(caja) {
        const t = caja.totales;
        const movs = caja.movimientos || [];

        let html = `
            <div class="alert alert-success mb-3">
                <i class="bi bi-unlock-fill"></i>
                <strong>Caja abierta</strong>
                <div class="small mt-1">
                    Apertura: ${esc(caja.fecha_apertura)} por ${esc(caja.abierta_por || '-')}
                </div>
            </div>

            <div class="row g-2 mb-3">
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center">
                        <div class="kpi-label small">Apertura</div>
                        <div class="fw-bold">${esc(t.monto_apertura_fmt)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center">
                        <div class="kpi-label small">Ventas efectivo</div>
                        <div class="fw-bold text-cobrado">${esc(t.ventas_efectivo_fmt)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center">
                        <div class="kpi-label small">Pagos efectivo</div>
                        <div class="fw-bold text-cobrado">${esc(t.pagos_efectivo_fmt)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center">
                        <div class="kpi-label small">Ingresos</div>
                        <div class="fw-bold text-cobrado">${esc(t.ingresos_fmt)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center">
                        <div class="kpi-label small">Retiros</div>
                        <div class="fw-bold text-pendiente">${esc(t.retiros_fmt)}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-kpi p-2 text-center" style="border: 2px solid var(--color-acento);">
                        <div class="kpi-label small">Esperado</div>
                        <div class="fw-bold fs-5">${esc(t.esperado_fmt)}</div>
                    </div>
                </div>
            </div>

            <div class="d-flex gap-2 mb-3 flex-wrap">
                <button type="button" class="btn btn-outline-success btn-sm fw-bold" id="btn-ingreso-manual">
                    <i class="bi bi-plus-circle"></i> Ingreso
                </button>
                <button type="button" class="btn btn-outline-danger btn-sm fw-bold" id="btn-retiro-manual">
                    <i class="bi bi-dash-circle"></i> Retiro
                </button>
            </div>

            <h5 class="mb-2"><i class="bi bi-list-ul"></i> Movimientos (${movs.length})</h5>
        `;

        if (movs.length === 0) {
            html += `<div class="alert alert-secondary mb-0">Aún no hay movimientos registrados en esta caja.</div>`;
        } else {
            html += `
                <div class="tabla-local">
                  <div class="table-responsive">
                    <table class="table table-sm align-middle mb-0">
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Tipo</th>
                                <th>Forma de pago</th>
                                <th>Descripción</th>
                                <th class="text-end">Monto</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            movs.forEach(m => {
                const colorTipo = m.tipo === 'RETIRO' ? 'text-pendiente' :
                                  m.tipo === 'INGRESO' ? 'text-cobrado' : '';
                const signo = m.tipo === 'RETIRO' ? '-' : '+';
                const badgeForma = m.forma_pago
                    ? `<span class="badge bg-info text-dark">${esc(m.forma_pago)}</span>`
                    : '<span class="texto-secundario small">-</span>';
                html += `
                    <tr class="${m.anulado ? 'opacity-50' : ''}">
                        <td class="small">${esc(m.fecha)}</td>
                        <td><span class="badge bg-secondary">${esc(m.tipo_display)}</span></td>
                        <td>${badgeForma}</td>
                        <td class="small">${esc(m.descripcion || '-')}</td>
                        <td class="text-end fw-bold ${colorTipo}">${signo} ${esc(m.monto_fmt)}</td>
                    </tr>
                `;
            });
            html += `</tbody></table></div></div>`;
        }

        modalBody.innerHTML = html;

        document.getElementById('btn-ingreso-manual').addEventListener('click', function () {
            modalCaja.hide();
            abrirModalMovimiento('INGRESO');
        });
        document.getElementById('btn-retiro-manual').addEventListener('click', function () {
            modalCaja.hide();
            abrirModalMovimiento('RETIRO');
        });

        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
            <button type="button" class="btn btn-danger fw-bold" id="btnCerrarCajaDesdeModal">
                <i class="bi bi-lock"></i> Cerrar caja
            </button>
        `;
        document.getElementById('btnCerrarCajaDesdeModal').addEventListener('click', function () {
            modalCaja.hide();
            abrirModalCerrar(caja);
        });
    }

    // ============================================================
    // Render: caja cerrada (última)
    // ============================================================
    function renderCajaCerrada(caja) {
        const tieneDif = caja.diferencia !== null && caja.diferencia !== 0;

        modalBody.innerHTML = `
            <div class="alert alert-secondary mb-3">
                <i class="bi bi-lock-fill"></i>
                <strong>Última caja cerrada</strong>
                <div class="small mt-1">
                    Cerrada el ${esc(caja.fecha_cierre)} por ${esc(caja.cerrada_por || '-')}
                </div>
            </div>

            <div class="row g-2 mb-3">
                <div class="col-md-6">
                    <div class="texto-secundario small">Monto esperado</div>
                    <div class="fw-bold">${esc(caja.monto_cierre_esperado_fmt)}</div>
                </div>
                <div class="col-md-6 text-end">
                    <div class="texto-secundario small">Monto real contado</div>
                    <div class="fw-bold">${esc(caja.monto_cierre_real_fmt)}</div>
                </div>
            </div>

            <div class="alert ${tieneDif ? 'alert-danger' : 'alert-success'} mb-3">
                <div class="d-flex justify-content-between">
                    <strong>Diferencia:</strong>
                    <strong>${esc(caja.diferencia_fmt)}</strong>
                </div>
                ${tieneDif ? `<div class="small mt-1">${esc(caja.observaciones || 'Sin observaciones')}</div>` : ''}
            </div>

            <p class="texto-secundario small mb-0">No hay caja abierta. Abrí una nueva para empezar el turno.</p>
        `;

        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary fw-bold" data-bs-dismiss="modal">
                <i class="bi bi-x-circle"></i> Cerrar
            </button>
            <button type="button" class="btn btn-success fw-bold" id="btnAbrirCajaDesdeModal">
                <i class="bi bi-unlock"></i> Abrir nueva caja
            </button>
        `;
        document.getElementById('btnAbrirCajaDesdeModal').addEventListener('click', function () {
            modalCaja.hide();
            abrirModalAbrir();
        });
    }

    // ============================================================
    // Modal: Abrir
    // ============================================================
    function abrirModalAbrir() {
        document.getElementById('formAbrirCaja').reset();
        document.getElementById('abrir-caja-error').style.display = 'none';
        document.getElementById('abrir-monto-apertura').value = '0';
        modalAbrir.show();
    }

    document.getElementById('btnAbrirCaja').addEventListener('click', async function () {
        const btn = this;
        const errorDiv = document.getElementById('abrir-caja-error');
        const form = document.getElementById('formAbrirCaja');
        const formData = new FormData(form);

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Abriendo…';
        errorDiv.style.display = 'none';

        try {
            const { ok, data } = await fetchJSON(urls.caja_abrir_api, {
                method: 'POST',
                body: formData,
            });
            if (!ok || !data.ok) throw new Error(data.error || 'Error al abrir caja');

            modalAbrir.hide();
            cajaActual = data.caja;
            actualizarBadge(cajaActual);
            actualizarTarjetaDashboard(cajaActual);
            setTimeout(() => modalCaja.show(), 300);
        } catch (err) {
            errorDiv.textContent = err.message;
            errorDiv.style.display = 'block';
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-unlock"></i> Abrir caja';
        }
    });

    // ============================================================
    // Modal: Cerrar
    // ============================================================
    function abrirModalCerrar(caja) {
        document.getElementById('formCerrarCaja').reset();
        document.getElementById('cerrar-caja-error').style.display = 'none';

        const t = caja.totales;
        document.getElementById('cerrar-resumen').innerHTML = `
            <div><strong>Apertura:</strong> ${esc(t.monto_apertura_fmt)}</div>
            <div><strong>Ventas efectivo:</strong> ${esc(t.ventas_efectivo_fmt)}</div>
            <div><strong>Pagos efectivo:</strong> ${esc(t.pagos_efectivo_fmt)}</div>
            <div><strong>Ingresos:</strong> ${esc(t.ingresos_fmt)}</div>
            <div><strong>Retiros:</strong> ${esc(t.retiros_fmt)}</div>
            <div class="mt-2"><strong>Esperado:</strong> <span class="fs-5 text-warning">${esc(t.esperado_fmt)}</span></div>
        `;

        document.getElementById('cerrar-monto-real').value = t.esperado;
        modalCerrar.show();
    }

    document.getElementById('btnCerrarCaja').addEventListener('click', async function () {
        const btn = this;
        const errorDiv = document.getElementById('cerrar-caja-error');
        const form = document.getElementById('formCerrarCaja');
        const formData = new FormData(form);

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cerrando…';
        errorDiv.style.display = 'none';

        try {
            const { ok, data } = await fetchJSON(urls.caja_cerrar_api, {
                method: 'POST',
                body: formData,
            });
            if (!ok || !data.ok) throw new Error(data.error || 'Error al cerrar caja');

            modalCerrar.hide();
            cajaActual = data.caja;
            actualizarBadge(cajaActual);
            actualizarTarjetaDashboard(cajaActual);
            setTimeout(() => modalCaja.show(), 300);
        } catch (err) {
            errorDiv.textContent = err.message;
            errorDiv.style.display = 'block';
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-lock"></i> Cerrar caja';
        }
    });

    // ============================================================
    // Modal: Movimiento
    // ============================================================
    function abrirModalMovimiento(tipo) {
        document.getElementById('formMovimientoCaja').reset();
        document.getElementById('movimiento-error').style.display = 'none';

        document.getElementById('movimiento-tipo').value = tipo;
        document.getElementById('movimiento-titulo').innerHTML =
            tipo === 'INGRESO'
                ? '<i class="bi bi-plus-circle text-success"></i> Ingreso manual'
                : '<i class="bi bi-dash-circle text-danger"></i> Retiro manual';

        if (tipo === 'INGRESO') {
            document.getElementById('tipo-ingreso').checked = true;
        } else {
            document.getElementById('tipo-retiro').checked = true;
        }

        modalMovimiento.show();
    }

    document.querySelectorAll('input[name="tipo_radio"]').forEach(radio => {
        radio.addEventListener('change', function () {
            document.getElementById('movimiento-tipo').value = this.value;
        });
    });

    document.getElementById('btnGuardarMovimiento').addEventListener('click', async function () {
        const btn = this;
        const errorDiv = document.getElementById('movimiento-error');
        const form = document.getElementById('formMovimientoCaja');
        const formData = new FormData(form);

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando…';
        errorDiv.style.display = 'none';

        try {
            const { ok, data } = await fetchJSON(urls.caja_movimiento_api, {
                method: 'POST',
                body: formData,
            });
            if (!ok || !data.ok) throw new Error(data.error || 'Error al guardar movimiento');

            modalMovimiento.hide();
            cajaActual = data.caja;
            actualizarTarjetaDashboard(cajaActual);
            setTimeout(() => modalCaja.show(), 300);
        } catch (err) {
            errorDiv.textContent = err.message;
            errorDiv.style.display = 'block';
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-circle"></i> Registrar';
        }
    });

    // ============================================================
    // Al abrir el modal, cargar estado
    // ============================================================
    modalCajaEl.addEventListener('show.bs.modal', function () {
        cargarEstado();
    });

    // ============================================================
    // Cargar estado inicial (badge + tarjeta)
    // ============================================================
    fetchJSON(urls.caja_actual_api)
        .then(({ ok, data }) => {
            if (ok && data.ok) {
                actualizarBadge(data.caja);
                actualizarTarjetaDashboard(data.caja);
            }
        })
        .catch(err => console.warn('[caja_modal] No se pudo cargar el estado inicial:', err));
});