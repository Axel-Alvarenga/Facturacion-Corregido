from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from ..models import Cliente, Venta, PagoDeuda


# =============================================================================
# INFORMES - PESTAÑA 1: Deudas por cliente
# =============================================================================

def _clientes_filtrados_deudas(request):
    """Aplica los filtros de la pestaña de deudas (reusable por el PDF).
    Ordena por nombre_local (alfabético) y luego por nombre."""
    buscar = request.GET.get('buscar', '').strip()
    solo_con_deuda = request.GET.get('solo_con_deuda', '') == '1'

    clientes = Cliente.objects.all().order_by('nombre_local', 'nombre')

    if buscar:
        clientes = clientes.filter(
            Q(nombre__icontains=buscar) |
            Q(nombre_local__icontains=buscar) |
            Q(telefono__icontains=buscar)
        )

    if solo_con_deuda:
        clientes = clientes.filter(deuda__gt=0)

    filtros = {
        'buscar': buscar,
        'solo_con_deuda': solo_con_deuda,
    }
    return clientes, filtros


@login_required(login_url='login')
def informes_deudas(request):
    """Pestaña de informes centrada en las deudas de los clientes."""
    clientes, filtros = _clientes_filtrados_deudas(request)

    total_clientes = Cliente.objects.count()
    clientes_con_deuda = Cliente.objects.filter(deuda__gt=0).count()
    monto_total_deuda = (
        Cliente.objects.filter(deuda__gt=0).aggregate(t=Sum('deuda'))['t']
        or Decimal('0.00')
    )

    context = {
        'pestaña_activa': 'deudas',
        'clientes': clientes,
        'total_clientes': total_clientes,
        'clientes_con_deuda': clientes_con_deuda,
        'monto_total_deuda': monto_total_deuda,
        'hoy': timezone.localdate(),
        **filtros,
    }
    return render(request, 'facturacion/informes/informes_deudas.html', context)


@login_required(login_url='login')
def informes_deudas_pdf(request):
    """Genera un PDF en hoja Oficio vertical, sin colores (para imprimir
    en blanco y negro). Incluye columnas en blanco para completar a mano.
    El orden de la lista es por nombre_local y luego por nombre."""
    from reportlab.lib.pagesizes import legal
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

    clientes, _ = _clientes_filtrados_deudas(request)
    clientes_lista = list(clientes)

    total_clientes_filtrados = len(clientes_lista)
    total_deuda_filtrada = sum(
        (c.deuda for c in clientes_lista if c.deuda > 0), Decimal('0.00')
    )

    response = HttpResponse(content_type='application/pdf')
    fecha_archivo = timezone.localdate().strftime('%Y-%m-%d')
    response['Content-Disposition'] = (
        f'attachment; filename="deudas_clientes_{fecha_archivo}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=legal,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title='Deudas por cliente',
        author='Comedor A.R.M.',
    )

    color_negro = colors.black
    color_gris_texto = colors.HexColor('#333333')
    color_gris_fondo = colors.HexColor('#E8E8E8')
    color_gris_suave = colors.HexColor('#F5F5F5')
    color_borde = colors.black

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'Titulo', parent=estilos['Heading1'], fontSize=14,
        textColor=color_negro, spaceAfter=2, alignment=TA_LEFT,
        fontName='Helvetica-Bold',
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Normal'], fontSize=8,
        textColor=color_gris_texto, alignment=TA_LEFT, spaceAfter=8,
    )
    estilo_celda = ParagraphStyle(
        'Celda', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, leading=10,
    )
    estilo_celda_centro = ParagraphStyle(
        'CeldaCentro', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, alignment=TA_CENTER, leading=10,
    )
    estilo_celda_right = ParagraphStyle(
        'CeldaRight', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, alignment=TA_RIGHT, leading=10,
    )
    estilo_celda_bold = ParagraphStyle(
        'CeldaBold', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold', leading=10,
    )
    estilo_celda_bold_right = ParagraphStyle(
        'CeldaBoldRight', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold',
        alignment=TA_RIGHT, leading=10,
    )
    estilo_celda_bold_centro = ParagraphStyle(
        'CeldaBoldCentro', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold',
        alignment=TA_CENTER, leading=10,
    )

    elementos = []
    elementos.append(Paragraph('Comedor A.R.M.', estilo_titulo))
    fecha_hoy = timezone.localtime()
    elementos.append(Paragraph(
        f'Informe de deudas por cliente — '
        f'Generado: {fecha_hoy.strftime("%d/%m/%Y %H:%M")}',
        estilo_subtitulo
    ))

    data = [[
        Paragraph('<b>Nombre</b>', estilo_celda_bold),
        Paragraph('<b>Frecuencia</b>', estilo_celda_bold_centro),
        Paragraph('<b>Deuda Total</b>', estilo_celda_bold_right),
        Paragraph('<b>Desayuno</b>', estilo_celda_bold_centro),
        Paragraph('<b>Almuerzo</b>', estilo_celda_bold_centro),
        Paragraph('<b>Total</b>', estilo_celda_bold_centro),
        Paragraph('<b>Estado</b>', estilo_celda_bold_centro),
    ]]

    for c in clientes_lista:
        nombre_con_local = c.nombre
        if c.nombre_local:
            nombre_con_local = f'{c.nombre} ({c.nombre_local})'

        frecuencia = '-'
        if c.tipo_pago == 'CREDITO':
            frecuencia = c.get_frecuencia_pago_display()

        deuda_texto = f'{c.deuda:,.0f}'.replace(',', '.') if c.deuda > 0 else '0'

        data.append([
            Paragraph(nombre_con_local, estilo_celda),
            Paragraph(frecuencia, estilo_celda_centro),
            Paragraph(deuda_texto, estilo_celda_right),
            Paragraph('', estilo_celda_centro),
            Paragraph('', estilo_celda_centro),
            Paragraph('', estilo_celda_centro),
            Paragraph('', estilo_celda_centro),
        ])

    total_texto = f'{total_deuda_filtrada:,.0f}'.replace(',', '.')
    data.append([
        Paragraph('<b>TOTAL GENERAL</b>', estilo_celda_bold),
        Paragraph('', estilo_celda),
        Paragraph(f'<b>{total_texto}</b>', estilo_celda_bold_right),
        Paragraph('', estilo_celda),
        Paragraph('', estilo_celda),
        Paragraph('', estilo_celda),
        Paragraph('', estilo_celda),
    ])

    col_widths = [
        62 * mm,
        20 * mm,
        26 * mm,
        22 * mm,
        22 * mm,
        22 * mm,
        22 * mm,
    ]

    tabla = Table(data, colWidths=col_widths, repeatRows=1)

    estilos_tabla = [
        ('BACKGROUND', (0, 0), (-1, 0), color_gris_fondo),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.8, color_borde),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, color_borde),
        ('BACKGROUND', (0, -1), (-1, -1), color_gris_fondo),
        ('LINEABOVE', (0, -1), (-1, -1), 1.2, color_borde),
    ]

    for i in range(1, len(clientes_lista) + 1):
        if i % 2 == 0:
            estilos_tabla.append(
                ('BACKGROUND', (0, i), (2, i), color_gris_suave)
            )

    tabla.setStyle(TableStyle(estilos_tabla))
    elementos.append(tabla)

    elementos.append(Spacer(1, 6))
    elementos.append(Paragraph(
        f'Total de registros: {total_clientes_filtrados}. '
        f'Las columnas Desayuno, Almuerzo, Total y Estado se completan a mano.',
        ParagraphStyle(
            'Pie', parent=estilos['Normal'], fontSize=7,
            textColor=color_gris_texto, alignment=TA_CENTER,
        )
    ))

    doc.build(elementos)
    return response


@login_required(login_url='login')
def informe_deuda_cliente_pdf(request, cliente_id):
    """Genera un PDF con el detalle de deuda de un cliente:
    - Datos del cliente (nombre, local, teléfono, frecuencia de pago)
    - Deuda actual
    - Historial de ventas a crédito NO anuladas con el detalle de productos
    - Saldo pendiente real por venta (descontando pagos FIFO)
    """
    from reportlab.lib.pagesizes import legal
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

    cliente = get_object_or_404(Cliente, pk=cliente_id)

    ventas_credito = (
        Venta.objects
        .filter(cliente=cliente, forma_pago='CREDITO', anulada=False)
        .prefetch_related('detalles__producto', 'items_manuales', 'pagos')
        .order_by('-fecha')
    )
    ventas_lista = list(ventas_credito)

    total_historico = sum((v.total for v in ventas_lista), Decimal('0.00'))

    response = HttpResponse(content_type='application/pdf')
    fecha_archivo = timezone.localdate().strftime('%Y-%m-%d')
    nombre_archivo = cliente.nombre.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = (
        f'attachment; filename="deuda_{nombre_archivo}_{fecha_archivo}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=legal,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f'Detalle de deuda - {cliente.nombre}',
        author='Comedor A.R.M.',
    )

    color_negro = colors.black
    color_gris_texto = colors.HexColor('#333333')
    color_gris_fondo = colors.HexColor('#E8E8E8')
    color_gris_suave = colors.HexColor('#F5F5F5')
    color_borde = colors.black

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'Titulo', parent=estilos['Heading1'], fontSize=16,
        textColor=color_negro, spaceAfter=2, alignment=TA_LEFT,
        fontName='Helvetica-Bold',
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Normal'], fontSize=9,
        textColor=color_gris_texto, alignment=TA_LEFT, spaceAfter=10,
    )
    estilo_label = ParagraphStyle(
        'Label', parent=estilos['Normal'], fontSize=9,
        textColor=color_gris_texto, leading=12,
    )
    estilo_valor = ParagraphStyle(
        'Valor', parent=estilos['Normal'], fontSize=10,
        textColor=color_negro, fontName='Helvetica-Bold', leading=13,
    )
    estilo_deuda = ParagraphStyle(
        'Deuda', parent=estilos['Normal'], fontSize=16,
        textColor=color_negro, fontName='Helvetica-Bold',
        alignment=TA_RIGHT, leading=18,
    )
    estilo_celda = ParagraphStyle(
        'Celda', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, leading=10,
    )
    estilo_celda_centro = ParagraphStyle(
        'CeldaCentro', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, alignment=TA_CENTER, leading=10,
    )
    estilo_celda_right = ParagraphStyle(
        'CeldaRight', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, alignment=TA_RIGHT, leading=10,
    )
    estilo_celda_bold = ParagraphStyle(
        'CeldaBold', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold', leading=10,
    )
    estilo_celda_bold_right = ParagraphStyle(
        'CeldaBoldRight', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold',
        alignment=TA_RIGHT, leading=10,
    )
    estilo_celda_bold_centro = ParagraphStyle(
        'CeldaBoldCentro', parent=estilos['Normal'], fontSize=8,
        textColor=color_negro, fontName='Helvetica-Bold',
        alignment=TA_CENTER, leading=10,
    )
    estilo_seccion = ParagraphStyle(
        'Seccion', parent=estilos['Heading2'], fontSize=11,
        textColor=color_negro, spaceAfter=6, fontName='Helvetica-Bold',
    )
    estilo_pie = ParagraphStyle(
        'Pie', parent=estilos['Normal'], fontSize=7,
        textColor=color_gris_texto, alignment=TA_LEFT,
    )

    elementos = []

    # ---- Encabezado ----
    elementos.append(Paragraph('Comedor A.R.M.', estilo_titulo))
    fecha_hoy = timezone.localtime()
    elementos.append(Paragraph(
        f'Detalle de deuda — Generado: {fecha_hoy.strftime("%d/%m/%Y %H:%M")}',
        estilo_subtitulo
    ))

    # ---- Datos del cliente ----
    nombre_con_local = cliente.nombre
    if cliente.nombre_local:
        nombre_con_local = f'{cliente.nombre} ({cliente.nombre_local})'

    frecuencia = '-'
    if cliente.tipo_pago == 'CREDITO':
        frecuencia = cliente.get_frecuencia_pago_display()

    telefono = cliente.telefono or '-'

    datos_cliente = [
        [
            Paragraph('Cliente:', estilo_label),
            Paragraph(nombre_con_local, estilo_valor),
        ],
        [
            Paragraph('Teléfono:', estilo_label),
            Paragraph(telefono, estilo_valor),
        ],
        [
            Paragraph('Frecuencia de pago:', estilo_label),
            Paragraph(frecuencia, estilo_valor),
        ],
    ]

    tabla_cliente = Table(datos_cliente, colWidths=[38 * mm, 136 * mm])
    tabla_cliente.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elementos.append(tabla_cliente)

    elementos.append(Spacer(1, 8))

    # ---- Deuda actual ----
    deuda_texto = f'{cliente.deuda:,.0f}'.replace(',', '.')
    tabla_deuda = Table(
        [[
            Paragraph('DEUDA ACTUAL:', estilo_valor),
            Paragraph(f'Gs. {deuda_texto}', estilo_deuda),
        ]],
        colWidths=[42 * mm, 132 * mm],
    )
    tabla_deuda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_gris_fondo),
        ('BOX', (0, 0), (-1, -1), 1.2, color_borde),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabla_deuda)

    elementos.append(Spacer(1, 12))

    # ---- Historial de ventas a crédito NO anuladas ----
    elementos.append(Paragraph(
        '<b>Historial de ventas a crédito</b>', estilo_seccion
    ))

    if not ventas_lista:
        elementos.append(Paragraph(
            'Este cliente no tiene ventas a crédito registradas.',
            estilo_subtitulo
        ))
    else:
        data = [[
            Paragraph('<b>#</b>', estilo_celda_bold_centro),
            Paragraph('<b>Fecha</b>', estilo_celda_bold_centro),
            Paragraph('<b>Productos</b>', estilo_celda_bold),
            Paragraph('<b>Total</b>', estilo_celda_bold_right),
            Paragraph('<b>Pagado</b>', estilo_celda_bold_right),
            Paragraph('<b>Pendiente</b>', estilo_celda_bold_right),
        ]]

        total_pendiente = Decimal('0.00')

        for v in ventas_lista:
            items_texto = []
            for d in v.detalles.all():
                subtotal = d.precio_unitario * d.cantidad
                items_texto.append(
                    f'{d.producto.nombre} x{d.cantidad} '
                    f'(Gs. {subtotal:,.0f})'
                )
            for m in v.items_manuales.all():
                items_texto.append(
                    f'{m.descripcion} (manual) (Gs. {m.precio:,.0f})'
                )
            if not items_texto:
                items_texto.append('(sin ítems)')

            productos_html = '<br/>'.join(
                t.replace(',', '.') for t in items_texto
            )

            pagado_venta = sum((p.monto for p in v.pagos.all()), Decimal('0.00'))
            pendiente_venta = v.total - pagado_venta
            if pendiente_venta < 0:
                pendiente_venta = Decimal('0.00')
            total_pendiente += pendiente_venta

            data.append([
                Paragraph(str(v.id), estilo_celda_centro),
                Paragraph(v.fecha.strftime('%d/%m/%Y'), estilo_celda_centro),
                Paragraph(productos_html, estilo_celda),
                Paragraph(
                    f'{v.total:,.0f}'.replace(',', '.'),
                    estilo_celda_right
                ),
                Paragraph(
                    f'{pagado_venta:,.0f}'.replace(',', '.'),
                    estilo_celda_right
                ),
                Paragraph(
                    f'{pendiente_venta:,.0f}'.replace(',', '.'),
                    estilo_celda_right
                ),
            ])

        total_hist_texto = f'{total_historico:,.0f}'.replace(',', '.')
        total_pend_texto = f'{total_pendiente:,.0f}'.replace(',', '.')
        data.append([
            Paragraph('', estilo_celda),
            Paragraph('', estilo_celda),
            Paragraph('<b>TOTALES</b>', estilo_celda_bold_right),
            Paragraph(f'<b>{total_hist_texto}</b>', estilo_celda_bold_right),
            Paragraph('', estilo_celda_bold_right),
            Paragraph(f'<b>{total_pend_texto}</b>', estilo_celda_bold_right),
        ])

        col_widths = [12 * mm, 20 * mm, 88 * mm, 22 * mm, 20 * mm, 22 * mm]
        tabla = Table(data, colWidths=col_widths, repeatRows=1)

        estilos_tabla = [
            ('BACKGROUND', (0, 0), (-1, 0), color_gris_fondo),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.8, color_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, color_borde),
            ('BACKGROUND', (0, -1), (-1, -1), color_gris_fondo),
            ('LINEABOVE', (0, -1), (-1, -1), 1.2, color_borde),
        ]

        for i in range(1, len(ventas_lista) + 1):
            if i % 2 == 0:
                estilos_tabla.append(
                    ('BACKGROUND', (0, i), (-1, i), color_gris_suave)
                )

        tabla.setStyle(TableStyle(estilos_tabla))
        elementos.append(tabla)

    elementos.append(Spacer(1, 8))
    elementos.append(Paragraph(
        'Nota: el historial muestra todas las ventas a crédito vigentes del cliente '
        '(las ventas anuladas no se incluyen). La columna "Pendiente" refleja el '
        'saldo real después de aplicar los pagos.',
        estilo_pie
    ))

    doc.build(elementos)
    return response


# =============================================================================
# INFORMES - PESTAÑA 2: Ventas del período
# =============================================================================

def _ventas_filtradas(request, incluir_anuladas=True):
    """Aplica los filtros de la pestaña de ventas.
    Por defecto incluye las ventas anuladas (para que el superusuario las vea).
    Los KPIs y resumen por forma de pago se calculan aparte, excluyéndolas.
    """
    ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')

    if not incluir_anuladas:
        ventas = ventas.filter(anulada=False)

    cliente_query = request.GET.get('cliente', '').strip()
    forma_pago_query = request.GET.get('forma_pago', '').strip()
    estado_query = request.GET.get('estado', '').strip()
    fecha_desde_query = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_query = request.GET.get('fecha_hasta', '').strip()

    if cliente_query:
        ventas = ventas.filter(cliente__nombre__icontains=cliente_query)
    if forma_pago_query:
        ventas = ventas.filter(forma_pago__iexact=forma_pago_query)
    if estado_query:
        ventas = ventas.filter(estado=estado_query)
    if fecha_desde_query:
        ventas = ventas.filter(fecha__date__gte=fecha_desde_query)
    if fecha_hasta_query:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta_query)

    filtros = {
        'cliente_query': cliente_query,
        'forma_pago_query': forma_pago_query,
        'estado_query': estado_query,
        'fecha_desde_query': fecha_desde_query,
        'fecha_hasta_query': fecha_hasta_query,
    }
    return ventas, filtros


def _pagos_filtrados(request):
    """Aplica los mismos filtros de fecha a los PagoDeuda del período.
    Solo considera pagos que apuntan a ventas NO anuladas (o pagos a cuenta
    sin venta, que no se anularon).
    """
    pagos = (
        PagoDeuda.objects
        .select_related('cliente', 'venta')
        .filter(Q(venta__isnull=True) | Q(venta__anulada=False))
    )

    fecha_desde_query = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_query = request.GET.get('fecha_hasta', '').strip()
    cliente_query = request.GET.get('cliente', '').strip()

    if fecha_desde_query:
        pagos = pagos.filter(fecha__date__gte=fecha_desde_query)
    if fecha_hasta_query:
        pagos = pagos.filter(fecha__date__lte=fecha_hasta_query)
    if cliente_query:
        pagos = pagos.filter(cliente__nombre__icontains=cliente_query)

    return pagos


@login_required(login_url='login')
def informes_ventas(request):
    """Pestaña de informes centrada en las ventas del período.
    - La TABLA muestra todas las ventas (incluidas las anuladas, con badge).
    - Los KPIs y el resumen por forma de pago EXCLUYEN las anuladas.
    """
    # Tabla: incluye anuladas (para que el superusuario las vea)
    ventas, filtros = _ventas_filtradas(request, incluir_anuladas=True)
    ventas_lista = list(ventas)

    # Para KPIs y resumen: solo no anuladas
    ventas_vigentes = [v for v in ventas_lista if not v.anulada]

    # Pagos del período (solo de ventas no anuladas)
    pagos = _pagos_filtrados(request)
    pagos_lista = list(pagos)

    total_filtrado = sum((v.total for v in ventas_vigentes), Decimal('0.00'))
    cantidad_filtrada = len(ventas_vigentes)
    ticket_promedio = (
        total_filtrado / cantidad_filtrada if cantidad_filtrada
        else Decimal('0.00')
    )

    # ============ COBRADO vs PENDIENTE ============
    # Efectivo: siempre cobrado
    efectivo_total = sum(
        (v.total for v in ventas_vigentes if v.forma_pago == 'EFECTIVO'),
        Decimal('0.00'),
    )

    # Transferencias: depende del estado
    transferencias_cobradas = sum(
        (v.total for v in ventas_vigentes
         if v.forma_pago == 'TRANSFERENCIA' and v.estado == 'CONFIRMADA'),
        Decimal('0.00'),
    )
    transferencias_pendientes = sum(
        (v.total for v in ventas_vigentes
         if v.forma_pago == 'TRANSFERENCIA' and v.estado == 'PENDIENTE'),
        Decimal('0.00'),
    )

    # Crédito del período (solo ventas vigentes)
    credito_total = sum(
        (v.total for v in ventas_vigentes if v.forma_pago == 'CREDITO'),
        Decimal('0.00'),
    )

    # Pendiente = crédito del período - pagos aplicados a esas ventas
    venta_ids_credito = {v.id for v in ventas_vigentes if v.forma_pago == 'CREDITO'}
    pagos_credito_ventas = sum(
        (p.monto for p in pagos_lista if p.venta_id in venta_ids_credito),
        Decimal('0.00'),
    )
    credito_pendiente = credito_total - pagos_credito_ventas
    if credito_pendiente < 0:
        credito_pendiente = Decimal('0.00')

    # Cobrado del crédito = TODOS los pagos del período (aunque sean de
    # ventas de otros períodos). Es plata que entró en el período.
    credito_cobrado = sum(
        (p.monto for p in pagos_lista),
        Decimal('0.00'),
    )

    # Totales
    total_cobrado = efectivo_total + transferencias_cobradas + credito_cobrado
    total_pendiente = credito_pendiente + transferencias_pendientes

    # Resumen por forma de pago
    resumen_forma_pago = {
        'EFECTIVO': {
            'cobrado': efectivo_total,
            'pendiente': Decimal('0.00'),
        },
        'CREDITO': {
            'cobrado': credito_cobrado,
            'pendiente': credito_pendiente,
        },
        'TRANSFERENCIA': {
            'cobrado': transferencias_cobradas,
            'pendiente': transferencias_pendientes,
        },
    }

    transferencias_pendientes_count = Venta.objects.filter(
        forma_pago='TRANSFERENCIA', estado='PENDIENTE', anulada=False
    ).count()

    hoy = timezone.localdate()

    context = {
        'pestaña_activa': 'ventas',
        'ventas': ventas_lista,
        'total_filtrado': total_filtrado,
        'cantidad_filtrada': cantidad_filtrada,
        'ticket_promedio': ticket_promedio,
        'total_cobrado': total_cobrado,
        'total_pendiente': total_pendiente,
        'resumen_forma_pago': resumen_forma_pago,
        'transferencias_pendientes_count': transferencias_pendientes_count,
        'hoy': hoy.isoformat(),
        'primer_dia_mes': hoy.replace(day=1).isoformat(),
        **filtros,
    }
    return render(request, 'facturacion/informes/informes_ventas.html', context)


# =============================================================================
# Export de ventas a Excel
# =============================================================================

@login_required(login_url='login')
def informes_export_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    ventas, _ = _ventas_filtradas(request, incluir_anuladas=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Informe de ventas'

    encabezados = [
        '# Venta', 'Cliente', 'Local', 'Fecha', 'Forma de pago',
        'Estado', 'Anulada', 'Total (Gs.)',
    ]
    ws.append(encabezados)

    relleno_encabezado = PatternFill(start_color='16232C', end_color='16232C', fill_type='solid')
    fuente_encabezado = Font(color='FFFFFF', bold=True)
    for col in range(1, len(encabezados) + 1):
        celda = ws.cell(row=1, column=col)
        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado
        celda.alignment = Alignment(horizontal='center')

    fila = 1
    for v in ventas:
        fila += 1
        ws.append([
            v.id,
            v.cliente.nombre,
            v.cliente.nombre_local or '-',
            v.fecha.strftime('%d/%m/%Y %H:%M'),
            v.get_forma_pago_display(),
            v.get_estado_display(),
            'Sí' if v.anulada else 'No',
            float(v.total),
        ])

    if fila > 1:
        fila_total = fila + 1
        ws.cell(row=fila_total, column=7, value='TOTAL').font = Font(bold=True)
        ws.cell(row=fila_total, column=8, value=f'=SUM(H2:H{fila})').font = Font(bold=True)

    anchos = [10, 25, 18, 18, 16, 16, 10, 16]
    for i, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="informe_ventas.xlsx"'
    wb.save(response)
    return response