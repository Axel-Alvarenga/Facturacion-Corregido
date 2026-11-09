/* =========================================================
   Comedor A.R.M. - Buscador en vivo para Clientes
   - Hace submit del formulario al dejar de escribir (debounce)
   - Mantiene el foco en el input después de recargar
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-buscador-clientes');
    const inputBuscar = document.getElementById('input-buscar-clientes');
    const checkboxDeuda = document.getElementById('solo_con_deuda');
    
    if (!form || !inputBuscar) return;

    // --- Mantener el foco al recargar la página por el buscador ---
    // Usamos sessionStorage para recordar que el foco estaba en el buscador
    const teniaFoco = sessionStorage.getItem('clientes_buscador_foco') === '1';
    
    if (teniaFoco) {
        inputBuscar.focus();
        // Ponemos el cursor al final del texto
        const len = inputBuscar.value.length;
        try {
            inputBuscar.setSelectionRange(len, len);
        } catch (e) {}
        sessionStorage.removeItem('clientes_buscador_foco');
    }

    // --- Switch "Solo con deuda" ---
    if (checkboxDeuda) {
        checkboxDeuda.addEventListener('change', function () {
            sessionStorage.setItem('clientes_buscador_foco', '1');
            form.submit();
        });
    }

    // --- Buscador con debounce ---
    let timeoutId = null;

    function guardarEstadoYEnviar() {
        sessionStorage.setItem('clientes_buscador_foco', '1');
        form.submit();
    }

    inputBuscar.addEventListener('input', function () {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(guardarEstadoYEnviar, 500); // Espera 500ms
    });

    inputBuscar.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(timeoutId);
            guardarEstadoYEnviar();
        }
    });
});