/* =========================================================
   Comedor A.R.M. - Aviso y cierre automático del sistema
   - Avisa X minutos antes de la hora de cierre.
   - Permite extender la sesión por X minutos.
   - Cierra sesión al llegar la hora.
   ========================================================= */

(function () {
    'use strict';

    // Configuración que viene inyectada desde base.html
    const config = window.__ARM_CIERRE_CONFIG__ || {};
    const HORA_CIERRE = config.horaCierre || 20;
    const MINUTOS_ANTES = config.minutosAntes || 5;
    const URL_LOGOUT = config.urlLogout || '/logout/';
    const URL_EXTENDER = config.urlExtender || '/extender-sesion/';
    const CSRF_TOKEN = config.csrfToken || '';

    let avisoMostrado = false;

    function minutosParaCierre() {
        const ahora = new Date();
        const cierre = new Date();
        cierre.setHours(HORA_CIERRE, 0, 0, 0);
        return Math.round((cierre - ahora) / 60000);
    }

    function cerrarSesionAhora() {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = URL_LOGOUT;
        const csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        csrf.value = CSRF_TOKEN;
        form.appendChild(csrf);
        document.body.appendChild(form);
        form.submit();
    }

    function extenderSesion(modal) {
        fetch(URL_EXTENDER, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        })
        .then(res => res.json())
        .then(data => {
            if (data.ok) {
                avisoMostrado = false;
                modal.hide();
                programarAviso(data.minutos);
            }
        })
        .catch(err => {
            console.error(err);
            alert('No se pudo extender la sesión.');
        });
    }

    function mostrarAviso() {
        if (avisoMostrado) return;
        avisoMostrado = true;

        const minutos = minutosParaCierre();
        const modalHtml = `
            <div class="modal fade" id="modalAvisoCierre" tabindex="-1" data-bs-backdrop="static">
              <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content confirmar-venta-modal">
                  <div class="modal-header border-0">
                    <h4 class="modal-title">
                      <i class="bi bi-exclamation-triangle text-warning"></i> El sistema está por cerrarse
                    </h4>
                  </div>
                  <div class="modal-body text-center">
                    <p class="fs-5 mb-3">El sistema se cierra en <strong id="avisar-minutos">${minutos}</strong> minuto(s).</p>
                    <p class="texto-secundario mb-0">
                      Podés extender el tiempo por 10 minutos más para terminar lo que estés haciendo.
                    </p>
                  </div>
                  <div class="modal-footer border-0 d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary fw-bold" id="btnCerrarSesionAhora">
                      <i class="bi bi-box-arrow-right"></i> Cerrar sesión ahora
                    </button>
                    <button type="button" class="btn btn-warning fw-bold" id="btnExtenderSesion">
                      <i class="bi bi-plus-circle"></i> Extender 10 minutos
                    </button>
                  </div>
                </div>
              </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalEl = document.getElementById('modalAvisoCierre');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();

        const intervalId = setInterval(() => {
            const m = minutosParaCierre();
            const el = document.getElementById('avisar-minutos');
            if (el) el.textContent = m;
            if (m <= 0) {
                clearInterval(intervalId);
                window.location.reload();
            }
        }, 30000);

        document.getElementById('btnCerrarSesionAhora').addEventListener('click', cerrarSesionAhora);
        document.getElementById('btnExtenderSesion').addEventListener('click', function () {
            extenderSesion(modal);
        });

        modalEl.addEventListener('hidden.bs.modal', function () {
            modalEl.remove();
        });
    }

    function programarAviso(minutosExtra) {
        const minutos = minutosExtra || minutosParaCierre() - MINUTOS_ANTES;
        if (minutos <= 0) {
            mostrarAviso();
            return;
        }
        setTimeout(mostrarAviso, minutos * 60 * 1000);
    }

    document.addEventListener('DOMContentLoaded', function () {
        const minutos = minutosParaCierre();
        if (minutos <= MINUTOS_ANTES && minutos > 0) {
            mostrarAviso();
        } else if (minutos > MINUTOS_ANTES) {
            const tiempoHastaAviso = (minutos - MINUTOS_ANTES) * 60 * 1000;
            setTimeout(mostrarAviso, tiempoHastaAviso);
        }
    });
})();