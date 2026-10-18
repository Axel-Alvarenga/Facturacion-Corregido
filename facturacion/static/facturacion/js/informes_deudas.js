/* =========================================================
   Comedor A.R.M. - Informe de deudas
   - Auto-filtrado al escribir en el buscador (debounce 500ms)
   - Auto-submit al cambiar el switch "Solo con deuda"
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-filtros-deudas');
    const inputBuscar = document.getElementById('input-buscar-deudas');
    const checkboxDeuda = document.getElementById('solo_con_deuda');
    if (!form) return;

    if (checkboxDeuda) {
        checkboxDeuda.addEventListener('change', function () {
            form.submit();
        });
    }

    if (inputBuscar) {
        let timeoutId = null;
        inputBuscar.addEventListener('input', function () {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(function () {
                form.submit();
            }, 500);
        });

        inputBuscar.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(timeoutId);
                form.submit();
            }
        });
    }
});