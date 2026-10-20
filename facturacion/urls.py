from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('extender-sesion/', views.extender_sesion, name='extender_sesion'),

    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/nuevo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', views.cliente_delete, name='cliente_delete'),
    path('clientes/pagar/<int:cliente_id>/', views.pagar_deuda, name='pagar_deuda'),

    path('productos/', views.producto_list, name='producto_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/editar/<int:pk>/', views.producto_update, name='producto_update'),
    path('productos/eliminar/<int:pk>/', views.producto_delete, name='producto_delete'),

    path('ventas/nueva/', views.crear_venta, name='crear_venta'),
    path('ventas/transferencias-pendientes/', views.transferencias_pendientes_api, name='transferencias_pendientes_api'),
    path('ventas/<int:venta_id>/confirmada/', views.venta_confirmada, name='venta_confirmada'),
    path('ventas/<int:venta_id>/ticket/', views.ticket_venta, name='ticket_venta'),
    path('ventas/<int:venta_id>/confirmar-transferencia/', views.confirmar_transferencia, name='confirmar_transferencia'),
    path('ventas/<int:venta_id>/detalle/', views.venta_detalle_api, name='venta_detalle_api'),
    path('ventas/<int:venta_id>/anular/', views.anular_venta, name='anular_venta'),

    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/nuevo/', views.pedido_create, name='pedido_create'),
    path('pedidos/<int:pk>/estado/<str:nuevo_estado>/', views.pedido_actualizar_estado, name='pedido_actualizar_estado'),

    path('api/buscar-productos/', views.buscar_productos, name='buscar_productos'),

    # ---- CAJA ----
    path('caja/actual/', views.caja_actual_api, name='caja_actual_api'),
    path('caja/abrir/', views.caja_abrir_api, name='caja_abrir_api'),
    path('caja/cerrar/', views.caja_cerrar_api, name='caja_cerrar_api'),
    path('caja/movimiento/', views.caja_movimiento_api, name='caja_movimiento_api'),
    path('caja/list/', views.caja_list_api, name='caja_list_api'),
    path('caja/<int:caja_id>/detalle/', views.caja_detalle_api, name='caja_detalle_api'),

    path('informes/', views.informes_deudas, name='informes'),
    path('informes/deudas/', views.informes_deudas, name='informes_deudas'),
    path('informes/deudas/pdf/', views.informes_deudas_pdf, name='informes_deudas_pdf'),
    path('informes/deudas/<int:cliente_id>/pdf/', views.informe_deuda_cliente_pdf, name='informe_deuda_cliente_pdf'),
    path('informes/ventas/', views.informes_ventas, name='informes_ventas'),
    path('informes/exportar-excel/', views.informes_export_excel, name='informes_export_excel'),

    path('auditoria/', views.auditoria_list, name='auditoria_list'),
    path('auditoria/exportar-excel/', views.auditoria_export_excel, name='auditoria_export_excel'),
    path('auditoria/<int:pk>/', views.auditoria_detalle, name='auditoria_detalle'),
]