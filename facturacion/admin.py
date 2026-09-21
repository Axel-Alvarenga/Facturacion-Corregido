from django.contrib import admin
from .models import Cliente, Producto, Venta, DetalleVenta, PedidoCocina, DetallePedido

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_local', 'tipo_pago', 'telefono')
    list_filter = ('tipo_pago',)
    search_fields = ('nombre', 'nombre_local')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'foto')
    search_fields = ('nombre',)

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'forma_pago', 'fecha', 'total')
    list_filter = ('forma_pago', 'fecha')
    inlines = [DetalleVentaInline]

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

@admin.register(PedidoCocina)
class PedidoCocinaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa_o_cliente', 'estado', 'fecha')
    list_filter = ('estado',)
    inlines = [DetallePedidoInline]