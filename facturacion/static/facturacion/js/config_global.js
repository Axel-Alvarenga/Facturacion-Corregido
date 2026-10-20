/* =========================================================
   Comedor A.R.M. - Configuración global para los JS
   - URLs de Django
   ========================================================= */

(function () {
    'use strict';

    function leerJSON(id) {
        const el = document.getElementById(id);
        if (!el) return {};
        try {
            return JSON.parse(el.textContent || '{}');
        } catch (err) {
            console.error('Error parseando JSON de #' + id + ':', err);
            return {};
        }
    }

    // Leer la configuración global que Django inyectó
    window.__ARM_URLS__ = leerJSON('arm-config-urls') || {};
})();