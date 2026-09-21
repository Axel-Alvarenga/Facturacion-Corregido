from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from ..models import Venta


def _ventas_filtradas(request):
    """Aplica los filtros de Informes (reusado también por la exportación a Excel)."""
    ventas = Venta.objects.select_related('cliente').all().order_by('-fecha')

    cliente_query = request.GET.get('cliente', '').strip()
    forma_pago_query = request.GET.get('forma_pago', '').strip()
    fecha_desde_query = request.GET.get('fecha_desde', '').strip()
    fecha_hasta_query = request.GET.get('fecha_hasta', '').strip()

    if cliente_query:
        ventas = ventas.filter(cliente__nombre__icontains=cliente_query)
    if forma_pago_query:
        ventas = ventas.filter(forma_pago__iexact=forma_pago_query)
    if fecha_desde_query:
        ventas = ventas.filter(fecha__date__gte=fecha_desde_query)
    if fecha_hasta_query:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta_query)

    filtros = {
        'cliente_query': cliente_query,
        'forma_pago_query': forma_pago_query,
        'fecha_desde_query': fecha_desde_query,
        'fecha_hasta_query': fecha_hasta_query,
    }
    return ventas, filtros


@login_required(login_url='login')
def informes(request):
    ventas, filtros = _ventas_filtradas(request)

    total_filtrado = sum(v.total for v in ventas)
    cantidad_filtrada = ventas.count()
    ticket_promedio = (total_filtrado / cantidad_filtrada) if cantidad_filtrada else Decimal('0.00')

    # Una sola consulta agrupada, en vez de una consulta por forma de pago.
    formas = dict(Venta._meta.get_field('forma_pago').choices)
    resumen_forma_pago = {codigo: Decimal('0.00') for codigo in formas}
    for fila in ventas.values('forma_pago').annotate(total=Sum('total')):
        resumen_forma_pago[fila['forma_pago']] = fila['total'] or Decimal('0.00')

    hoy = timezone.localdate()

    context = {
        'ventas': ventas,
        'total_filtrado': total_filtrado,
        'cantidad_filtrada': cantidad_filtrada,
        'ticket_promedio': ticket_promedio,
        'resumen_forma_pago': resumen_forma_pago,
        'hoy': hoy.isoformat(),
        'primer_dia_mes': hoy.replace(day=1).isoformat(),
        **filtros,
    }
    return render(request, 'facturacion/informes/informes.html', context)


@login_required(login_url='login')
def informes_export_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    ventas, _ = _ventas_filtradas(request)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Informe de ventas'

    encabezados = ['# Venta', 'Cliente', 'Local', 'Fecha', 'Forma de pago', 'Total (Gs.)']
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
            float(v.total),
        ])

    if fila > 1:
        fila_total = fila + 1
        ws.cell(row=fila_total, column=5, value='TOTAL').font = Font(bold=True)
        ws.cell(row=fila_total, column=6, value=f'=SUM(F2:F{fila})').font = Font(bold=True)

    anchos = [10, 25, 18, 18, 16, 16]
    for i, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="informe_ventas.xlsx"'
    wb.save(response)
    return response