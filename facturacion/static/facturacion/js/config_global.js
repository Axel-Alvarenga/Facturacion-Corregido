/* =========================================================
   Comedor A.R.M. - Configuración global para los JS
   - URLs de Django
   - Configuración de cierre automático
   ========================================================= */

(function () {
    'use strict';

    // Función helper para leer un JSON del HTML
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
    window.__ARM_CIERRE_CONFIG__ = leerJSON('arm-config-cierre') || {};

    // Valores por defecto por si algo falla
    if (!window.__ARM_CIERRE_CONFIG__.horaCierre) {
        window.__ARM_CIERRE_CONFIG__.horaCierre = 20;
    }
    if (!window.__ARM_CIERRE_CONFIG__.minutosAntes) {
        window.__ARM_CIERRE_CONFIG__.minutosAntes = 5;
    }
})();