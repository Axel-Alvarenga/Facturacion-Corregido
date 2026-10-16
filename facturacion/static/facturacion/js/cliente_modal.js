/* =========================================================
   Comedor A.R.M. - Modal de Cliente (crear / editar)
   - La frecuencia de pago solo se muestra si tipo_pago = CREDITO
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalCliente');
    if (!modalEl) return;

    const form = document.getElementById('form-cliente-modal');
    const titulo = document.getElementById('modalClienteTituloTexto');
    const iconoTitulo = modalEl.querySelector('.modal-title i');

    const inputNombre = document.getElementById('id_nombre_cliente');
    const inputNombreLocal = document.getElementById('id_nombre_local');
    const selectTipoPago = document.getElementById('id_tipo_pago');
    const selectFrecuenciaPago = document.getElementById('id_frecuencia_pago');
    const bloqueFrecuencia = document.getElementById('bloque-frecuencia-pago');
    const inputTelefono = document.getElementById('id_telefono');

    // Leer los datos que Django puso en el JSON del HTML
    const datosModalRaw = document.getElementById('datos-modal-cliente');
    const datosModal = datosModalRaw ? JSON.parse(datosModalRaw.textContent || '{}') : {};

    const urlsBase = {
        crear: "/clientes/nuevo/",
        editar: "/clientes/" // se completa con el id
    };

    // ============================================================
    // Mostrar/ocultar la frecuencia de pago según la preferencia
    // ============================================================
    function actualizarVisibilidadFrecuencia() {
        const esCredito = selectTipoPago.value === 'CREDITO';
        if (esCredito) {
            bloqueFrecuencia.style.display = 'block';
            // Si el select no tiene valor o está vacío, dejamos el primero (Semanal)
            if (!selectFrecuenciaPago.value) {
                selectFrecuenciaPago.value = 'SEMANAL';
            }
        } else {
            bloqueFrecuencia.style.display = 'none';
            // Si no es crédito, forzamos frecuencia CONTADO
            // (el modelo acepta CONTADO; no se muestra en el select pero se envía)
            // Dejamos el select como está para no romper la validación del form
        }
    }

    // Escuchar cambios en el select de tipo_pago
    if (selectTipoPago) {
        selectTipoPago.addEventListener('change', actualizarVisibilidadFrecuencia);
    }

    // ============================================================
    // Al abrir el modal
    // ============================================================
    modalEl.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        const modo = boton ? boton.dataset.modo : (datosModal.modal_activo || 'crear');

        if (modo === 'editar') {
            const id = boton ? boton.dataset.id : datosModal.objeto_id;
            const nombre = boton ? boton.dataset.nombre : datosModal.valores.nombre;
            const nombreLocal = boton ? boton.dataset.nombreLocal : datosModal.valores.nombre_local;
            const tipoPago = boton ? boton.dataset.tipoPago : datosModal.valores.tipo_pago;
            const frecuenciaPago = boton ? boton.dataset.frecuenciaPago : datosModal.valores.frecuencia_pago;
            const telefono = boton ? boton.dataset.telefono : datosModal.valores.telefono;

            titulo.textContent = 'Editar Cliente';
            iconoTitulo.className = 'bi bi-pencil text-warning';
            inputNombre.value = nombre || '';
            inputNombreLocal.value = nombreLocal || '';
            inputTelefono.value = telefono || '';

            // tipo_pago
            const tipoPagoFinal = (tipoPago || 'CONTADO').toUpperCase();
            for (let opt of selectTipoPago.options) {
                opt.selected = (opt.value === tipoPagoFinal);
            }

            // frecuencia_pago (solo si es crédito)
            const frecuenciaPagoFinal = (frecuenciaPago || 'SEMANAL').toUpperCase();
            for (let opt of selectFrecuenciaPago.options) {
                opt.selected = (opt.value === frecuenciaPagoFinal);
            }

            form.action = urlsBase.editar + id + '/editar/';
        } else {
            titulo.textContent = 'Nuevo Cliente';
            iconoTitulo.className = 'bi bi-person-plus text-warning';
            form.action = urlsBase.crear;
            inputNombre.value = '';
            inputNombreLocal.value = '';
            inputTelefono.value = '';
            selectTipoPago.value = 'CONTADO';
            selectFrecuenciaPago.value = 'SEMANAL'; // valor por defecto si algún día se activa
        }

        // Después de cargar los valores, actualizar la visibilidad
        actualizarVisibilidadFrecuencia();
    });

    // Foco en el primer input al abrir el modal
    modalEl.addEventListener('shown.bs.modal', function () {
        inputNombre.focus();
    });

    // ============================================================
    // Validación y ajuste antes de enviar
    // ============================================================
    form.addEventListener('submit', function (e) {
        if (!inputNombre.value.trim()) {
            e.preventDefault();
            alert('Ingresá un nombre.');
            inputNombre.focus();
            return;
        }

        // Si NO es crédito, forzamos frecuencia_pago = CONTADO para no ensuciar
        if (selectTipoPago.value !== 'CREDITO') {
            selectFrecuenciaPago.value = 'CONTADO';
        }
        // Si ES crédito y por algún motivo no hay valor, forzamos SEMANAL
        else if (!selectFrecuenciaPago.value) {
            selectFrecuenciaPago.value = 'SEMANAL';
        }
    });

    // Abrir el modal automáticamente si la vista lo pidió (por errores)
    if (datosModal.modal_activo === 'crear' || datosModal.modal_activo === 'editar') {
        setTimeout(function () {
            const m = bootstrap.Modal.getOrCreateInstance(modalEl);
            m.show();
        }, 100);
    }
});