from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

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

    path('pedidos/', views.pedido_list, name='pedido_list'),
    path('pedidos/nuevo/', views.pedido_create, name='pedido_create'),
    path('pedidos/<int:pk>/estado/<str:nuevo_estado>/', views.pedido_actualizar_estado, name='pedido_actualizar_estado'),

    path('api/buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('informes/', views.informes, name='informes'),
    path('informes/exportar-excel/', views.informes_export_excel, name='informes_export_excel'),
]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)