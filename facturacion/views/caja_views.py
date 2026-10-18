from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import Caja, MovimientoCaja, Venta, PagoDeuda


def _serializar_decimal(valor):
    """Convierte un Decimal a float (para JSON)."""
    if valor is None:
        return None
    return float(valor)


def _formatear_gs(valor):
    """Formatea un número como 'Gs. 12.345'."""
    if valor is None:
        return 'Gs. 0'
    return f'Gs. {valor:,.0f}'.replace(',', '.')


def _caja_a_dict(caja, incluir_movimientos=False):
    """Serializa una caja a dict para JSON."""
    totales = caja.calcular_totales() if caja else {}

    data = {
        'id': caja.id,
        'estado': caja.estado,
        'estado_display': caja.get_estado_display(),
        'fecha_apertura': caja.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
        'abierta_por': caja.abierta_por.username if caja.abierta_por else None,
        'monto_apertura': _serializar_decimal(caja.monto_apertura),
        'monto_apertura_fmt': _formatear_gs(caja.monto_apertura),
        'fecha_cierre': caja.fecha_cierre.strftime('%d/%m/%Y %H:%M') if caja.fecha_cierre else None,
        'cerrada_por': caja.cerrada_por.username if caja.cerrada_por else None,
        'monto_cierre_real': _serializar_decimal(caja.monto_cierre_real),
        'monto_cierre_real_fmt': _formatear_gs(caja.monto_cierre_real) if caja.monto_cierre_real is not None else None,
        'monto_cierre_esperado': _serializar_decimal(caja.monto_cierre_esperado),
        'monto_cierre_esperado_fmt': _formatear_gs(caja.monto_cierre_esperado) if caja.monto_cierre_esperado is not None else None,
        'diferencia': _serializar_decimal(caja.diferencia),
        'diferencia_fmt': _formatear_gs(caja.diferencia) if caja.diferencia is not None else None,
        'observaciones': caja.observaciones,
        'totales': {
            'monto_apertura': _serializar_decimal(totales.get('monto_apertura')),
            'monto_apertura_fmt': _formatear_gs(totales.get('monto_apertura')),
            'ventas_efectivo': _serializar_decimal(totales.get('ventas_efectivo')),
            'ventas_efectivo_fmt': _formatear_gs(totales.get('ventas_efectivo')),
            'pagos_efectivo': _serializar_decimal(totales.get('pagos_efectivo')),
            'pagos_efectivo_fmt': _formatear_gs(totales.get('pagos_efectivo')),
            'ingresos': _serializar_decimal(totales.get('ingresos')),
            'ingresos_fmt': _formatear_gs(totales.get('ingresos')),
            'retiros': _serializar_decimal(totales.get('retiros')),
            'retiros_fmt': _formatear_gs(totales.get('retiros')),
            'esperado': _serializar_decimal(totales.get('esperado')),
            'esperado_fmt': _formatear_gs(totales.get('esperado')),
        },
    }

    if incluir_movimientos:
        movs = []
        for m in caja.movimientos.select_related('usuario', 'venta').all().order_by('-fecha'):
            movs.append({
                'id': m.id,
                'tipo': m.tipo,
                'tipo_display': m.get_tipo_display(),
                'forma_pago': m.forma_pago,
                'monto': _serializar_decimal(m.monto),
                'monto_fmt': _formatear_gs(m.monto),
                'descripcion': m.descripcion,
                'fecha': m.fecha.strftime('%d/%m/%Y %H:%M'),
                'usuario': m.usuario.username if m.usuario else None,
                'venta_id': m.venta_id,
                'anulado': m.anulado,
            })
        data['movimientos'] = movs

    return data


# =============================================================================
# CAJA ACTUAL
# =============================================================================

@login_required(login_url='login')
def caja_actual_api(request):
    """Devuelve el estado actual de la caja (abierta o cerrada).
    Si hay una caja abierta, devuelve el detalle + movimientos.
    Si no, devuelve la última caja cerrada (para referencia) o null.
    """
    caja = Caja.caja_abierta()

    if caja:
        return JsonResponse({
            'ok': True,
            'hay_caja_abierta': True,
            'caja': _caja_a_dict(caja, incluir_movimientos=True),
        })

    # No hay caja abierta: devolver la última cerrada (si existe)
    ultima = Caja.objects.filter(estado='CERRADA').order_by('-fecha_cierre').first()
    return JsonResponse({
        'ok': True,
        'hay_caja_abierta': False,
        'caja': _caja_a_dict(ultima) if ultima else None,
    })


# =============================================================================
# ABRIR CAJA
# =============================================================================

@login_required(login_url='login')
def caja_abrir_api(request):
    """Abre una caja con el monto inicial especificado.
    Solo puede haber una caja abierta a la vez.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    # Verificar que no haya otra caja abierta
    if Caja.caja_abierta():
        return JsonResponse({
            'ok': False,
            'error': 'Ya hay una caja abierta. Cerrá la caja actual antes de abrir otra.',
        }, status=400)

    monto_str = request.POST.get('monto_apertura', '').strip()
    observaciones = request.POST.get('observaciones', '').strip()

    try:
        monto = Decimal(monto_str) if monto_str else Decimal('0.00')
    except (InvalidOperation, TypeError):
        return JsonResponse({'ok': False, 'error': 'Monto inicial inválido.'}, status=400)

    if monto < 0:
        return JsonResponse({'ok': False, 'error': 'El monto inicial no puede ser negativo.'}, status=400)

    with transaction.atomic():
        caja = Caja.objects.create(
            monto_apertura=monto,
            abierta_por=request.user,
            observaciones=observaciones,
            estado='ABIERTA',
        )

    return JsonResponse({
        'ok': True,
        'mensaje': f'Caja abierta con Gs. {monto:,.0f}.',
        'caja': _caja_a_dict(caja, incluir_movimientos=True),
    })


# =============================================================================
# CERRAR CAJA
# =============================================================================

@login_required(login_url='login')
def caja_cerrar_api(request):
    """Cierra la caja abierta con el monto real contado."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    caja = Caja.caja_abierta()
    if not caja:
        return JsonResponse({'ok': False, 'error': 'No hay caja abierta para cerrar.'}, status=400)

    monto_str = request.POST.get('monto_cierre_real', '').strip()
    observaciones = request.POST.get('observaciones', '').strip()

    try:
        monto_real = Decimal(monto_str) if monto_str else Decimal('0.00')
    except (InvalidOperation, TypeError):
        return JsonResponse({'ok': False, 'error': 'Monto de cierre inválido.'}, status=400)

    if monto_real < 0:
        return JsonResponse({'ok': False, 'error': 'El monto de cierre no puede ser negativo.'}, status=400)

    totales = caja.calcular_totales()
    esperado = totales['esperado']
    diferencia = monto_real - esperado

    # Si hay diferencia, exigir observación
    if diferencia != 0 and not observaciones:
        return JsonResponse({
            'ok': False,
            'error': (
                f'Hay una diferencia de {_formatear_gs(diferencia)}. '
                f'Es obligatorio indicar una observación explicando la diferencia.'
            ),
        }, status=400)

    with transaction.atomic():
        caja.fecha_cierre = timezone.now()
        caja.monto_cierre_real = monto_real
        caja.monto_cierre_esperado = esperado
        caja.diferencia = diferencia
        caja.cerrada_por = request.user
        caja.estado = 'CERRADA'
        caja.observaciones = observaciones
        caja.save()

    return JsonResponse({
        'ok': True,
        'mensaje': (
            f'Caja cerrada. '
            f'Esperado: {_formatear_gs(esperado)}. '
            f'Real: {_formatear_gs(monto_real)}. '
            f'Diferencia: {_formatear_gs(diferencia)}.'
        ),
        'caja': _caja_a_dict(caja, incluir_movimientos=True),
    })


# =============================================================================
# MOVIMIENTO MANUAL (INGRESO / RETIRO)
# =============================================================================

@login_required(login_url='login')
def caja_movimiento_api(request):
    """Registra un ingreso o retiro manual en la caja abierta."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    caja = Caja.caja_abierta()
    if not caja:
        return JsonResponse({
            'ok': False,
            'error': 'No hay caja abierta. Abrí una caja primero.',
        }, status=400)

    tipo = request.POST.get('tipo', '').strip().upper()
    if tipo not in ('INGRESO', 'RETIRO'):
        return JsonResponse({
            'ok': False,
            'error': 'Tipo inválido. Debe ser INGRESO o RETIRO.',
        }, status=400)

    monto_str = request.POST.get('monto', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()

    if not descripcion:
        return JsonResponse({'ok': False, 'error': 'La descripción es obligatoria.'}, status=400)

    try:
        monto = Decimal(monto_str) if monto_str else Decimal('0.00')
    except (InvalidOperation, TypeError):
        return JsonResponse({'ok': False, 'error': 'Monto inválido.'}, status=400)

    if monto <= 0:
        return JsonResponse({'ok': False, 'error': 'El monto debe ser mayor a 0.'}, status=400)

    with transaction.atomic():
        mov = MovimientoCaja.objects.create(
            caja=caja,
            tipo=tipo,
            monto=monto,
            descripcion=descripcion[:300],
            usuario=request.user,
        )

    return JsonResponse({
        'ok': True,
        'mensaje': f'{mov.get_tipo_display()} de {_formatear_gs(monto)} registrado.',
        'caja': _caja_a_dict(caja, incluir_movimientos=True),
    })


# =============================================================================
# HISTORIAL DE CAJAS CERRADAS
# =============================================================================

@login_required(login_url='login')
def caja_list_api(request):
    """Devuelve el listado de cajas cerradas (para el modal de historial)."""
    cajas = Caja.objects.filter(estado='CERRADA').order_by('-fecha_cierre')

    data = []
    for c in cajas:
        data.append({
            'id': c.id,
            'fecha_apertura': c.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
            'fecha_cierre': c.fecha_cierre.strftime('%d/%m/%Y %H:%M') if c.fecha_cierre else None,
            'abierta_por': c.abierta_por.username if c.abierta_por else None,
            'cerrada_por': c.cerrada_por.username if c.cerrada_por else None,
            'monto_apertura_fmt': _formatear_gs(c.monto_apertura),
            'monto_cierre_real_fmt': _formatear_gs(c.monto_cierre_real),
            'monto_cierre_esperado_fmt': _formatear_gs(c.monto_cierre_esperado),
            'diferencia': _serializar_decimal(c.diferencia),
            'diferencia_fmt': _formatear_gs(c.diferencia),
            'tiene_diferencia': c.diferencia is not None and c.diferencia != 0,
        })

    return JsonResponse({'ok': True, 'cajas': data})


# =============================================================================
# DETALLE DE UNA CAJA
# =============================================================================

@login_required(login_url='login')
def caja_detalle_api(request, caja_id):
    """Devuelve el detalle completo de una caja (con movimientos)."""
    caja = get_object_or_404(Caja, pk=caja_id)
    return JsonResponse({
        'ok': True,
        'caja': _caja_a_dict(caja, incluir_movimientos=True),
    })