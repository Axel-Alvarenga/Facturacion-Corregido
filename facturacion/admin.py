from django.contrib import admin
from .models import (
    Cliente,
    Producto,
    Venta,
    DetalleVenta,
    ItemVentaManual,
    PedidoCocina,
    DetallePedido,
    PagoDeuda,
    RegistroAuditoria,
)


# =========================================================
# Cliente
# =========================================================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_local', 'tipo_pago', 'telefono', 'deuda')
    list_filter = ('tipo_pago',)
    search_fields = ('nombre', 'nombre_local', 'telefono')
    ordering = ('nombre',)


# =========================================================
# Producto
# =========================================================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'foto')
    search_fields = ('nombre',)
    ordering = ('nombre',)


# =========================================================
# Venta
# =========================================================
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('precio_unitario',)


class ItemVentaManualInline(admin.TabularInline):
    model = ItemVentaManual
    extra = 0


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'forma_pago', 'fecha', 'total')
    list_filter = ('forma_pago', 'fecha')
    search_fields = ('cliente__nombre', 'id')
    date_hierarchy = 'fecha'
    inlines = [DetalleVentaInline, ItemVentaManualInline]
    readonly_fields = ('fecha',)


# =========================================================
# Pedido a Cocina
# =========================================================
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0


@admin.register(PedidoCocina)
class PedidoCocinaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa_o_cliente', 'estado', 'fecha')
    list_filter = ('estado', 'fecha')
    search_fields = ('mesa_o_cliente',)
    date_hierarchy = 'fecha'
    inlines = [DetallePedidoInline]
    readonly_fields = ('fecha',)


# =========================================================
# Pago de deuda
# =========================================================
@admin.register(PagoDeuda)
class PagoDeudaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'monto', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('cliente__nombre',)
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha',)


# =========================================================
# Auditoría (solo lectura)
# =========================================================
@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha',
        'usuario',
        'accion',
        'modelo',
        'objeto_id',
        'objeto_repr',
        'ip',
    )
    list_filter = ('accion', 'modelo', 'fecha', 'usuario')
    search_fields = ('objeto_repr', 'usuario__username', 'modelo', 'ip')
    date_hierarchy = 'fecha'
    readonly_fields = (
        'fecha',
        'usuario',
        'accion',
        'modelo',
        'objeto_id',
        'objeto_repr',
        'cambios',
        'ip',
        'user_agent',
        'metadata',
    )
    ordering = ('-fecha',)

    def has_add_permission(self, request):
        # No se pueden crear registros de auditoría a mano
        return False

    def has_change_permission(self, request, obj=None):
        # No se pueden editar
        return False

    def has_delete_permission(self, request, obj=None):
        # Permitimos borrar solo a superusuarios (para limpieza manual)
        return request.user.is_superuser