from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from ..models import Cliente, Venta


# =============================================================================
# INFORMES - PESTAÑA 1: Deudas por cliente
# =============================================================================

def _clientes_filtrados_deudas(request):
    """Aplica los filtros de la pestaña de deudas (reusable por el PDF)."""
    buscar = request.GET.get('buscar', '').strip()
    solo_con_deuda = request.GET.get('solo_con_deuda', '') == '1'

    clientes = Cliente.objects.all().order_by('nombre', 'nombre_local')

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
        Cliente.objects.aggregate(t=Sum('deuda'))['t'] or Decimal('0.00')
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
    en blanco y negro). Incluye columnas en blanco para completar a mano."""
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
        (c.deuda for c in clientes_lista), Decimal('0.00')
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
        62 * mm, 20 * mm, 26 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm,
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


# =============================================================================
# INFORMES - PESTAÑA 2: Ventas del período
# =============================================================================

def _ventas_filtradas(request):
    """Aplica los filtros de la pestaña de ventas."""
    ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')

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


@login_required(login_url='login')
def informes_ventas(request):
    """Pestaña de informes centrada en las ventas del período."""
    ventas, filtros = _ventas_filtradas(request)

    total_filtrado = sum(v.total for v in ventas)
    cantidad_filtrada = ventas.count()
    ticket_promedio = (
        total_filtrado / cantidad_filtrada if cantidad_filtrada
        else Decimal('0.00')
    )

    formas = dict(Venta._meta.get_field('forma_pago').choices)
    resumen_forma_pago = {codigo: Decimal('0.00') for codigo in formas}
    for fila in ventas.values('forma_pago').annotate(total=Sum('total')):
        resumen_forma_pago[fila['forma_pago']] = fila['total'] or Decimal('0.00')

    transferencias_pendientes_count = Venta.objects.filter(
        forma_pago='TRANSFERENCIA', estado='PENDIENTE'
    ).count()

    hoy = timezone.localdate()

    context = {
        'pestaña_activa': 'ventas',
        'ventas': ventas,
        'total_filtrado': total_filtrado,
        'cantidad_filtrada': cantidad_filtrada,
        'ticket_promedio': ticket_promedio,
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

    ventas, _ = _ventas_filtradas(request)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Informe de ventas'

    encabezados = ['# Venta', 'Cliente', 'Local', 'Fecha', 'Forma de pago', 'Estado', 'Total (Gs.)']
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
            float(v.total),
        ])

    if fila > 1:
        fila_total = fila + 1
        ws.cell(row=fila_total, column=6, value='TOTAL').font = Font(bold=True)
        ws.cell(row=fila_total, column=7, value=f'=SUM(G2:G{fila})').font = Font(bold=True)

    anchos = [10, 25, 18, 18, 16, 16, 16]
    for i, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="informe_ventas.xlsx"'
    wb.save(response)
    return response