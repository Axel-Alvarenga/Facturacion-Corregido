/* =========================================================
   Comedor A.R.M. - Atajos de teclado globales
   ========================================================= */

(function () {
    'use strict';

    function initAtajosNavegacion() {
        const mapa = {
            '1': 'dashboard',
            '2': 'crear_venta',
            '3': 'pedido_list',
            '4': 'cliente_list',
            '5': 'producto_list',
            '6': 'informes',
            'v': 'crear_venta',
            'p': 'pedido_create',
            'n': 'producto_create',
            'c': 'cliente_create',
        };

        const urls = window.__ARM_URLS__ || {};

        document.addEventListener('keydown', function (e) {
            if (e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
                const k = e.key.toLowerCase();
                const nombre = mapa[k];
                if (nombre && urls[nombre]) {
                    e.preventDefault();
                    window.location.href = urls[nombre];
                }
            }
        });
    }

    function initEscapeModales() {
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.show').forEach(function (m) {
                    const modal = bootstrap.Modal.getInstance(m);
                    if (modal) modal.hide();
                });
            }
        });
    }

    function initCtrlEnter() {
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const form = document.querySelector('form[id^="form-"]') ||
                             document.querySelector('form');
                if (form) {
                    e.preventDefault();
                    form.requestSubmit();
                }
            }
        });
    }

    function initBuscadores() {
        document.querySelectorAll('[data-autocomplete]').forEach(function (input) {
            const contenedorId = input.dataset.resultados;
            const contenedor = document.getElementById(contenedorId);
            if (!contenedor) return;

            let indice = -1;

            function marcarActivo() {
                const items = contenedor.querySelectorAll('a');
                items.forEach((el, i) => el.classList.toggle('active', i === indice));
                // Hacer scroll al item activo si está fuera de la vista
                if (indice >= 0 && items[indice]) {
                    items[indice].scrollIntoView({ block: 'nearest' });
                }
            }

            input.addEventListener('keydown', function (e) {
                const items = contenedor.querySelectorAll('a');
                if (items.length === 0) return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    indice = (indice + 1) % items.length;
                    marcarActivo();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    indice = (indice - 1 + items.length) % items.length;
                    marcarActivo();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (indice >= 0 && items[indice]) {
                        items[indice].click();
                    } else if (items.length >= 1) {
                        items[0].click();
                    }
                } else if (e.key === 'Escape') {
                    contenedor.innerHTML = '';
                    input.value = '';
                }
            });

            input.addEventListener('blur', function () {
                indice = -1;
            });
        });
    }

    function initFocoInicial() {
        function aplicarFoco() {
            const inputProd = document.getElementById('buscar-prod');
            if (inputProd && document.activeElement !== inputProd) {
                inputProd.focus();
                return true;
            }

            const form = document.querySelector('form[id^="form-"]');
            if (form) {
                const primer = form.querySelector(
                    'input:not([type="hidden"]), select, textarea'
                );
                if (primer && document.activeElement !== primer) {
                    primer.focus();
                    return true;
                }
            }
            return false;
        }

        setTimeout(aplicarFoco, 50);
        setTimeout(aplicarFoco, 200);
        setTimeout(aplicarFoco, 500);
    }

    function initEnterEnTabla() {
        const tabla = document.getElementById('cuerpo-tabla');
        const inputProd = document.getElementById('buscar-prod');
        if (!tabla || !inputProd) return;

        tabla.addEventListener('keydown', function (e) {
            const esCantidad = e.target.classList.contains('cantidad-input') ||
                               e.target.name === 'cantidad[]';
            const esNota = e.target.name === 'nota_item[]';

            if (e.key !== 'Enter' || (!esCantidad && !esNota)) return;

            e.preventDefault();

            const filaActual = e.target.closest('tr');
            const filas = tabla.querySelectorAll('tr');
            const esUltimaFila = filaActual === filas[filas.length - 1];

            if (esUltimaFila) {
                const botonVender = document.getElementById('btn-vender');
                if (botonVender) {
                    botonVender.focus();
                }
            } else {
                inputProd.focus();
            }
        });

        tabla.addEventListener('click', function (e) {
            if (e.target.closest('.btn-eliminar') || e.target.closest('.btn-eliminar-manual')) {
                setTimeout(function () { inputProd.focus(); }, 10);
            }
        });
    }

    function initEnterEnVender() {
        const btnVender = document.getElementById('btn-vender');
        if (!btnVender) return;

        btnVender.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                btnVender.click();
            }
        });
    }

    function initAyuda() {
        document.addEventListener('keydown', function (e) {
            if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                const tag = (document.activeElement || {}).tagName;
                if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

                e.preventDefault();
                alert(
                    "Atajos de teclado:\n\n" +
                    "Alt + 1  → Inicio\n" +
                    "Alt + 2  → Nueva venta\n" +
                    "Alt + 3  → Pedidos\n" +
                    "Alt + 4  → Clientes\n" +
                    "Alt + 5  → Productos\n" +
                    "Alt + 6  → Informes\n\n" +
                    "Alt + V  → Nueva venta\n" +
                    "Alt + P  → Nuevo pedido\n" +
                    "Alt + N  → Nuevo producto\n" +
                    "Alt + C  → Nuevo cliente\n\n" +
                    "Ctrl + Enter  → Enviar formulario\n" +
                    "Esc           → Cerrar modal / sugerencias\n\n" +
                    "En buscadores:\n" +
                    "  ↑ ↓   → Moverse entre sugerencias\n" +
                    "  Enter → Seleccionar\n" +
                    "  Esc   → Cerrar\n\n" +
                    "En la tabla de productos:\n" +
                    "  Enter en una fila del medio → vuelve al buscador\n" +
                    "  Enter en la última fila → botón VENDER"
                );
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initAtajosNavegacion();
        initEscapeModales();
        initCtrlEnter();
        initBuscadores();
        initFocoInicial();
        initEnterEnTabla();
        initEnterEnVender();
        initAyuda();
    });
})();