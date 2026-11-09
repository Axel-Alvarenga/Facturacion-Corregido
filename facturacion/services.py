from decimal import Decimal
from django.db.models import Sum
from .models import PagoDeuda, Venta, Caja, MovimientoCaja

def aplicar_pago_fifo(cliente, monto_total, usuario, forma_pago='EFECTIVO'):
    """Aplica un pago a las ventas a crédito del cliente en orden FIFO.
    Crea un PagoDeuda por cada venta afectada.
    Devuelve la lista de PagoDeuda creados.
    """
    monto_restante = Decimal(monto_total)
    pagos_creados = []

    ventas_credito = (
        Venta.objects
        .filter(cliente=cliente, forma_pago='CREDITO', anulada=False)
        .order_by('fecha')
    )

    for venta in ventas_credito:
        if monto_restante <= 0:
            break

        pagado_venta = (
            PagoDeuda.objects
            .filter(venta=venta)
            .aggregate(total=Sum('monto'))['total']
            or Decimal('0.00')
        )
        saldo_venta = venta.total - pagado_venta

        if saldo_venta <= 0:
            continue

        monto_aplicar = min(monto_restante, saldo_venta)

        pago = PagoDeuda.objects.create(
            cliente=cliente,
            venta=venta,
            monto=monto_aplicar,
            forma_pago=forma_pago,
            registrado_por=usuario,
        )
        pagos_creados.append(pago)
        monto_restante -= monto_aplicar

    # Si sobró monto (cliente CREDITO pagó de más), registrar saldo a favor
    if monto_restante > 0:
        pago = PagoDeuda.objects.create(
            cliente=cliente,
            venta=None,
            monto=monto_restante,
            forma_pago=forma_pago,
            registrado_por=usuario,
            observacion='Saldo a favor (pago mayor a la deuda)',
        )
        pagos_creados.append(pago)

    return pagos_creados


def registrar_movimiento_caja_pago(cliente, monto_pago, forma_pago, usuario, pagos_creados):
    """Registra el movimiento de ingreso en la caja abierta (si existe)."""
    caja = Caja.caja_abierta()
    if caja:
        MovimientoCaja.objects.create(
            caja=caja,
            tipo='PAGO',
            forma_pago=forma_pago,
            monto=monto_pago,
            descripcion=f'Pago de deuda - {cliente.nombre} - {dict(PagoDeuda.FORMA_PAGO_CHOICES)[forma_pago]}',
            usuario=usuario,
            pago_deuda=pagos_creados[0] if pagos_creados else None,
        )