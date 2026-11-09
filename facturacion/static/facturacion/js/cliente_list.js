/* =========================================================
   Comedor A.R.M. - Listado de clientes
   - Modal de eliminación (rellenar nombre + action)
   - Atajo: Enter en la página (sin foco en inputs) abre el modal de Nuevo Cliente
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

    // ---- Modal de eliminación ----
    const modalEliminar = document.getElementById('modalEliminarCliente');
    if (modalEliminar) {
        modalEliminar.addEventListener('show.bs.modal', function (event) {
            const boton = event.relatedTarget;
            if (!boton) return;

            const clienteId = boton.getAttribute('data-id');
            const fila = document.getElementById('fila-cliente-' + clienteId);
            
            let nombreCliente = 'este cliente';
            let urlEliminar = '';

            // Si encontramos la fila, sacamos el nombre de ahí
            if (fila) {
                nombreCliente = fila.dataset.nombre || 'este cliente';
            }
            
            // La URL la armamos dinámicamente o la leemos del botón
            const urlData = boton.getAttribute('data-url');
            if (urlData) {
                urlEliminar = urlData;
            } else {
                urlEliminar = '/clientes/' + clienteId + '/eliminar/';
            }

            document.getElementById('modalEliminarClienteNombre').textContent = nombreCliente;
            document.getElementById('formEliminarCliente').action = urlEliminar;
        });
    }

    // ---- Enter en la página abre el modal de Nuevo Cliente ----
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;

        // Si ya hay un modal abierto, no hacer nada
        if (document.querySelector('.modal.show')) return;

        const el = document.activeElement;
        const tag = el ? el.tagName : '';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
            return;
        }
        if (tag === 'BUTTON' || tag === 'A') {
            return;
        }

        e.preventDefault();
        const modalEl = document.getElementById('modalCliente');
        if (modalEl) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    });
});