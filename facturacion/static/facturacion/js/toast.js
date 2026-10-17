/* =========================================================
   Comedor A.R.M. - Auto-mostrar toasts al cargar
   ========================================================= */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const toasts = document.querySelectorAll('#toast-container .toast');
        if (toasts.length === 0) return;

        toasts.forEach(function (t, i) {
            const toast = new bootstrap.Toast(t, {
                autohide: true,
                delay: 3500
            });
            // Pequeño delay escalonado para que aparezcan uno tras otro
            setTimeout(function () {
                toast.show();
            }, i * 150);
        });
    });
})();