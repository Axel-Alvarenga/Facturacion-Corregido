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
    
    // Corregido: seleccionar el ícono dentro del título
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
        const modo = boton ? boton.dataset.modo : 'crear';

        if (avisoDuplicado) avisoDuplicado.style.display = 'none';
        if (confirmarDuplicadoInput) confirmarDuplicadoInput.value = '';

        if (modo === 'editar') {
            const clienteId = boton.dataset.id;
            // Buscamos la fila de la tabla para extraer los datos de forma segura
            const fila = document.getElementById('fila-cliente-' + clienteId);
            
            titulo.textContent = 'Editar Cliente';
            iconoTitulo.className = 'bi bi-pencil text-warning';
            form.action = urlsBase.editar + clienteId + '/editar/';

            if (fila) {
                // Leemos los datos de la fila
                inputNombre.value = fila.dataset.nombre || '';
                inputNombreLocal.value = fila.dataset.nombreLocal || '';
                inputTelefono.value = fila.dataset.telefono || '';
                
                const tipoPago = (fila.dataset.tipoPago || 'CONTADO').toUpperCase();
                for (let opt of selectTipoPago.options) {
                    opt.selected = (opt.value === tipoPago);
                }
                
                const frecuenciaPago = (fila.dataset.frecuenciaPago || 'SEMANAL').toUpperCase();
                for (let opt of selectFrecuenciaPago.options) {
                    opt.selected = (opt.value === frecuenciaPago);
                }
            }
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
                window.location.reload();
            } else if (status === 409 && data.duplicado) {
                avisoDuplicadoTexto.textContent = ' ' + data.mensaje;
                avisoDuplicado.style.display = 'block';
                avisoDuplicado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else if (data.errors) {
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

    if (btnConfirmarDuplicado) {
        btnConfirmarDuplicado.addEventListener('click', function () {
            if (confirmarDuplicadoInput) confirmarDuplicadoInput.value = '1';
            enviarFormulario();
        });
    }
});