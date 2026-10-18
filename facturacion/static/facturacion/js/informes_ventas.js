/* =========================================================
   Comedor A.R.M. - Informe de ventas
   - Modal de confirmación de transferencia (custom, sin alert)
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    const modalConfTransf = document.getElementById('modalConfirmarTransferencia');
    if (!modalConfTransf) return;

    modalConfTransf.addEventListener('show.bs.modal', function (event) {
        const boton = event.relatedTarget;
        if (!boton) return;

        const ventaId = boton.getAttribute('data-venta-id');
        const ventaTotal = boton.getAttribute('data-venta-total');
        const ventaCliente = boton.getAttribute('data-venta-cliente');

        document.getElementById('conf-transf-venta-id').textContent = '#' + ventaId;
        document.getElementById('conf-transf-cliente').textContent = ventaCliente;
        document.getElementById('conf-transf-monto').textContent = ventaTotal;

        const form = document.getElementById('formConfirmarTransferencia');
        form.action = '/ventas/' + ventaId + '/confirmar-transferencia/';
    });
});