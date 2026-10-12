/* =========================================================
   Comedor A.R.M. - Modal de Producto (crear / editar)
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

    // Leer los datos que Django puso en el JSON del HTML
    const datosModalRaw = document.getElementById('datos-modal-producto');
    const datosModal = datosModalRaw ? JSON.parse(datosModalRaw.textContent || '{}') : {};

    const urlsBase = {
        crear: "/productos/nuevo/",
        editar: "/productos/editar/" // se completa con el id
    };

    // Al abrir el modal (ya sea con click o programáticamente)
    modalEl.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        const modo = boton ? boton.dataset.modo : (datosModal.modal_activo || 'crear');

        if (modo === 'editar') {
            const id = boton ? boton.dataset.id : datosModal.objeto_id;
            const nombre = boton ? boton.dataset.nombre : datosModal.valores.nombre;
            const precio = boton ? boton.dataset.precio : datosModal.valores.precio;
            const fotoUrl = boton ? boton.dataset.fotoUrl : '';

            titulo.textContent = 'Editar Producto';
            iconoTitulo.className = 'bi bi-pencil text-warning';
            inputNombre.value = nombre || '';

            // Convertir el precio a un número limpio
            const precioNum = precio !== undefined && precio !== ''
                ? parseFloat(precio)
                : null;
            inputPrecio.value = (precioNum !== null && !isNaN(precioNum)) ? precioNum : '';

            inputFoto.value = ''; // no se puede precargar por seguridad
            form.action = urlsBase.editar + id + '/';

            // Mostrar foto actual si existe
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

    // Foco en el primer input al abrir el modal
    modalEl.addEventListener('shown.bs.modal', function () {
        inputNombre.focus();
    });

    // Vista previa al seleccionar una nueva foto
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

    // Botón "Quitar" la foto seleccionada
    btnQuitar.addEventListener('click', function () {
        inputFoto.value = '';
        preview.src = '';
        previewWrapper.style.display = 'none';
        textoFotoActual.textContent = '';
    });

    // Al enviar: validación mínima del lado del cliente
    form.addEventListener('submit', function (e) {
        if (!inputNombre.value.trim()) {
            e.preventDefault();
            alert('Ingresá un nombre.');
            inputNombre.focus();
            return;
        }
        if (!inputPrecio.value || parseFloat(inputPrecio.value) < 0) {
            e.preventDefault();
            alert('Ingresá un precio válido.');
            inputPrecio.focus();
            return;
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