/* =========================================================
   Comedor A.R.M. - Modal de Producto (crear / editar)
   - Manejo robusto de respuestas
   - Detección de duplicado sin cerrar el modal
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalProducto');
    if (!modalEl) return;

    const form = document.getElementById('form-producto-modal');
    const titulo = document.getElementById('modalProductoTituloTexto');
    const iconoTitulo = modalEl.querySelector('.modal-title i');

    const inputNombre = document.getElementById('id_nombre');
    const inputPrecio = document.getElementById('id_precio');
    const inputFoto = document.getElementById('id_foto');

    const previewWrapper = document.getElementById('fotoPreviewWrapper');
    const preview = document.getElementById('fotoPreview');
    const btnQuitar = document.getElementById('btnQuitarFoto');
    const textoFotoActual = document.getElementById('fotoActualTexto');

    const avisoError = document.getElementById('producto-aviso-error');
    const avisoErrorTexto = document.getElementById('producto-aviso-error-texto');

    // Leer los datos que Django puso en el JSON del HTML (con manejo de errores)
    let datosModal = {};
    const datosModalRaw = document.getElementById('datos-modal-producto');
    if (datosModalRaw) {
        try {
            datosModal = JSON.parse(datosModalRaw.textContent || '{}');
        } catch (err) {
            console.error('No se pudo parsear el JSON del modal:', err);
            console.error('Contenido:', datosModalRaw.textContent);
            datosModal = {};
        }
    }

    const urlsBase = {
        crear: "/productos/nuevo/",
        editar: "/productos/editar/"
    };

    let enviando = false;

    modalEl.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        const modo = boton ? boton.dataset.modo : (datosModal.modal_activo || 'crear');

        // Ocultar aviso de error
        if (avisoError) avisoError.style.display = 'none';

        if (modo === 'editar') {
            const id = boton ? boton.dataset.id : datosModal.objeto_id;
            const nombre = boton ? boton.dataset.nombre : datosModal.valores.nombre;
            const precio = boton ? boton.dataset.precio : datosModal.valores.precio;
            const fotoUrl = boton ? boton.dataset.fotoUrl : '';

            titulo.textContent = 'Editar Producto';
            iconoTitulo.className = 'bi bi-pencil text-warning';
            inputNombre.value = nombre || '';

            const precioNum = precio !== undefined && precio !== ''
                ? parseFloat(precio)
                : null;
            inputPrecio.value = (precioNum !== null && !isNaN(precioNum)) ? precioNum : '';

            inputFoto.value = '';
            form.action = urlsBase.editar + id + '/';

            if (fotoUrl) {
                preview.src = fotoUrl;
                previewWrapper.style.display = 'block';
                textoFotoActual.textContent = 'Ya tiene una foto. Elegí una nueva para reemplazarla.';
            } else {
                previewWrapper.style.display = 'none';
                preview.src = '';
                textoFotoActual.textContent = '';
            }
        } else {
            titulo.textContent = 'Nuevo Producto';
            iconoTitulo.className = 'bi bi-plus-circle text-warning';
            form.action = urlsBase.crear;
            inputNombre.value = '';
            inputPrecio.value = '';
            inputFoto.value = '';
            previewWrapper.style.display = 'none';
            preview.src = '';
            textoFotoActual.textContent = '';
        }
    });

    modalEl.addEventListener('shown.bs.modal', function () {
        inputNombre.focus();
    });

    inputFoto.addEventListener('change', function () {
        const archivo = this.files[0];
        if (!archivo) {
            if (!preview.src) previewWrapper.style.display = 'none';
            return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            previewWrapper.style.display = 'block';
            textoFotoActual.textContent = '';
        };
        reader.readAsDataURL(archivo);
    });

    btnQuitar.addEventListener('click', function () {
        inputFoto.value = '';
        preview.src = '';
        previewWrapper.style.display = 'none';
        textoFotoActual.textContent = '';
    });

    // ============================================
    // Envío por AJAX con manejo de errores
    // ============================================
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (enviando) return;

        // Validación mínima
        if (!inputNombre.value.trim()) {
            alert('Ingresá un nombre.');
            inputNombre.focus();
            return;
        }
        if (!inputPrecio.value || parseFloat(inputPrecio.value) < 0) {
            alert('Ingresá un precio válido.');
            inputPrecio.focus();
            return;
        }

        enviando = true;

        // Ocultar aviso previo
        if (avisoError) avisoError.style.display = 'none';

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
            } else if (data.errors) {
                // Errores del form: mostrar sin cerrar
                let mensajes = [];
                Object.keys(data.errors).forEach(function (campo) {
                    mensajes.push(data.errors[campo].join(' '));
                });
                if (avisoError && avisoErrorTexto) {
                    avisoErrorTexto.textContent = ' ' + mensajes.join(' ');
                    avisoError.style.display = 'block';
                    avisoError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    alert(mensajes.join('\n'));
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo guardar.'));
            }
        })
        .catch((err) => {
            enviando = false;
            console.error(err);
            alert('Error: ' + err.message);
        });
    });

    if (datosModal.modal_activo === 'crear' || datosModal.modal_activo === 'editar') {
        setTimeout(function () {
            const m = bootstrap.Modal.getOrCreateInstance(modalEl);
            m.show();
        }, 100);
    }
});