/* =========================================================
   Comedor A.R.M. - Modal de Cliente (crear / editar)
   - Detección de duplicado sin cerrar el modal
   - Manejo robusto de respuestas no-JSON
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
    const confirmarDuplicadoInput = document.getElementById('cliente-confirmar-duplicado');

    const avisoDuplicado = document.getElementById('cliente-aviso-duplicado');
    const avisoDuplicadoTexto = document.getElementById('cliente-aviso-duplicado-texto');
    const btnConfirmarDuplicado = document.getElementById('btn-confirmar-duplicado');

    const datosModalRaw = document.getElementById('datos-modal-cliente');
    const datosModal = datosModalRaw ? JSON.parse(datosModalRaw.textContent || '{}') : {};

    const urlsBase = {
        crear: "/clientes/nuevo/",
        editar: "/clientes/"
    };

    let enviando = false;

    function actualizarVisibilidadFrecuencia() {
        if (selectTipoPago && selectTipoPago.value === 'CREDITO') {
            bloqueFrecuencia.style.display = 'block';
        } else {
            bloqueFrecuencia.style.display = 'none';
        }
    }

    if (selectTipoPago) {
        selectTipoPago.addEventListener('change', actualizarVisibilidadFrecuencia);
    }

    modalEl.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        const modo = boton ? boton.dataset.modo : (datosModal.modal_activo || 'crear');

        if (avisoDuplicado) avisoDuplicado.style.display = 'none';
        if (confirmarDuplicadoInput) confirmarDuplicadoInput.value = '';

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

            const tipoPagoFinal = (tipoPago || 'CONTADO').toUpperCase();
            for (let opt of selectTipoPago.options) {
                opt.selected = (opt.value === tipoPagoFinal);
            }

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
            selectFrecuenciaPago.value = 'SEMANAL';
        }

        actualizarVisibilidadFrecuencia();
    });

    modalEl.addEventListener('shown.bs.modal', function () {
        inputNombre.focus();
    });

    // ============================================
    // Envío por AJAX (con manejo de duplicado)
    // ============================================
    function enviarFormulario() {
        if (enviando) return;
        enviando = true;

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
            credentials: 'same-origin',
        })
        .then(async (res) => {
            const texto = await res.text();
            let data = null;
            try {
                data = JSON.parse(texto);
            } catch (err) {
                console.error('Respuesta no JSON del servidor:', texto.substring(0, 500));
                throw new Error('El servidor devolvió una respuesta inesperada.');
            }
            return { status: res.status, data };
        })
        .then(({ status, data }) => {
            enviando = false;

            if (status === 200 && data.ok) {
                // Éxito: recargar la lista
                window.location.reload();
            } else if (status === 409 && data.duplicado) {
                // Duplicado: mostrar aviso SIN cerrar el modal
                avisoDuplicadoTexto.textContent = ' ' + data.mensaje;
                avisoDuplicado.style.display = 'block';
                avisoDuplicado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else if (data.errors) {
                // Errores del form: mostrar sin cerrar
                let mensajes = [];
                Object.keys(data.errors).forEach(function (campo) {
                    mensajes.push(data.errors[campo].join(' '));
                });
                alert(mensajes.join('\n'));
            } else {
                alert('Error: ' + (data.error || 'No se pudo guardar.'));
            }
        })
        .catch((err) => {
            enviando = false;
            console.error(err);
            alert('Error: ' + err.message);
        });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (!inputNombre.value.trim()) {
            alert('Ingresá un nombre.');
            inputNombre.focus();
            return;
        }
        if (!inputNombreLocal.value.trim()) {
            alert('Ingresá el local (podés poner "Particular" si no tiene).');
            inputNombreLocal.focus();
            return;
        }

        enviarFormulario();
    });

    // Botón "Sí, crear de todos modos" → envía con confirmar_duplicado=1, SIN cerrar el modal
    if (btnConfirmarDuplicado) {
        btnConfirmarDuplicado.addEventListener('click', function () {
            if (confirmarDuplicadoInput) confirmarDuplicadoInput.value = '1';
            enviarFormulario();
        });
    }

    if (datosModal.modal_activo === 'crear' || datosModal.modal_activo === 'editar') {
        setTimeout(function () {
            const m = bootstrap.Modal.getOrCreateInstance(modalEl);
            m.show();
        }, 100);
    }
});