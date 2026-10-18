/* =========================================================
   Comedor A.R.M. - Informe de deudas
   - Auto-filtrado al escribir en el buscador (debounce 500ms)
   - Auto-submit al cambiar el switch "Solo con deuda"
   - Recupera el foco y la posición del cursor al recargar
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-filtros-deudas');
    const inputBuscar = document.getElementById('input-buscar-deudas');
    const checkboxDeuda = document.getElementById('solo_con_deuda');
    if (!form) return;

    // ---- Recuperar foco y cursor si venimos de un auto-submit ----
    const teniaFoco = sessionStorage.getItem('deudas_buscador_foco') === '1';
    const cursorPos = parseInt(sessionStorage.getItem('deudas_buscador_cursor') || '0', 10);

    if (teniaFoco && inputBuscar) {
        inputBuscar.focus();
        try {
            inputBuscar.setSelectionRange(cursorPos, cursorPos);
        } catch (e) {
            // Algunos navegadores no permiten setSelectionRange en type="text"?
            // En la práctica sí funciona, pero por si acaso.
        }
        sessionStorage.removeItem('deudas_buscador_foco');
        sessionStorage.removeItem('deudas_buscador_cursor');
    }

    // ---- Switch "Solo con deuda" ----
    if (checkboxDeuda) {
        checkboxDeuda.addEventListener('change', function () {
            form.submit();
        });
    }

    // ---- Buscador con debounce ----
    if (inputBuscar) {
        let timeoutId = null;

        function guardarEstadoYEnviar() {
            // Guardar en sessionStorage que el foco estaba en el buscador
            // y la posición del cursor, para recuperarlo al recargar
            sessionStorage.setItem('deudas_buscador_foco', '1');
            sessionStorage.setItem('deudas_buscador_cursor', String(inputBuscar.selectionStart || 0));
            form.submit();
        }

        inputBuscar.addEventListener('input', function () {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(guardarEstadoYEnviar, 500);
        });

        inputBuscar.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(timeoutId);
                guardarEstadoYEnviar();
            }
        });
    }
});