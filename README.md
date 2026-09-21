# App "facturacion" (Django) — sistema para el local

Módulos: Dashboard, login, ABM de clientes y productos (con borrado por
modal), ventas con búsqueda de producto/cliente en vivo, cuenta corriente
por cliente, Pedidos a Cocina, e Informes de Ventas unificado (KPIs,
filtros por rango de fecha, impresión y exportación a Excel).

## Instalación

1. `pip install django openpyxl`
2. `django-admin startproject sistema_local .` (si todavía no tenés el proyecto creado)
3. `python manage.py startapp facturacion` y reemplazar `models.py`,
   `forms.py`, `views.py`, `urls.py`, `admin.py`, `context_processors.py`
   por los de este paquete; copiar la carpeta `templates/facturacion/`
   dentro de `facturacion/templates/facturacion/`
4. En `settings.py`:
   - Agregar `'facturacion'` a `INSTALLED_APPS`
   - Agregar `'facturacion.context_processors.pedidos_pendientes_nav'` a la
     lista `context_processors` dentro de `TEMPLATES` (es la que alimenta
     el globito rojo de "Pedidos" en la barra de navegación)
   - Si vas a usar fotos de producto, configurar `MEDIA_URL`/`MEDIA_ROOT`
5. En `sistema_local/urls.py`:
   ```python
   from django.urls import path, include
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('facturacion.urls')),
   ]
   ```
6. `python manage.py makemigrations && python manage.py migrate`
   (esta vez la migración es más grande: se agregan los modelos de Pedidos
   y `Cliente.tipo_pago` pasa a tener opciones fijas — si ya tenías datos
   cargados con un valor de `tipo_pago` que no sea EFECTIVO/CREDITO/
   TRANSFERENCIA, Django te va a pedir que definas un valor por defecto
   para esa migración)
7. `python manage.py createsuperuser`
8. `python manage.py runserver`

## Rutas

- `/` — Dashboard (pantalla de inicio con las tarjetas grandes)
- Login / logout: `/login/`, `/logout/`
- Clientes (ABM completo, borrado por modal): `/clientes/`
- Productos (ABM completo, borrado por modal): `/productos/`
- Cobrar/abonar deuda de un cliente: `/clientes/pagar/<id>/`
- Nueva venta: `/ventas/nueva/`
- **Pedidos a Cocina**: `/pedidos/` (vista de cocina) y `/pedidos/nuevo/` (alta)
- **Ventas / Informes (unificado)**: `/informes/` — reemplaza al antiguo
  listado de ventas; ahí están las KPIs, los filtros y los botones de
  imprimir/exportar

## Qué cambió en esta vuelta

- **Se arregló el select roto de "Tipo de pago" en Clientes.** El campo
  usaba un `<select>` de Bootstrap pero el modelo no tenía opciones
  definidas, así que se veía vacío/deformado. Ahora usa las mismas
  opciones que la forma de pago de una venta (Efectivo/Crédito/Transferencia).
- **Ventas e Informes se unificaron en una sola pantalla** (`/informes/`).
  El listado de ventas viejo (`/ventas/`) desapareció.
- **Nuevo módulo de Pedidos a Cocina**, con una vista tipo pizarra
  (Pendiente / En preparación / Listo) para que la cocina vaya moviendo
  cada pedido. **Ojo:** esto se actualiza solo, recargando la página cada
  20 segundos — no es un canal en vivo (WebSocket). Para algo realmente en
  tiempo real (sin recargar) haría falta sumar Django Channels, que es una
  pieza de infraestructura más grande; si el local llega a necesitarlo por
  volumen, es el siguiente paso natural.
- **Nuevo Dashboard** como página de inicio (`/`), con tarjetas grandes
  para Nueva Venta, Pedidos, Productos, Clientes e Informes.
- **El buscador de productos ahora sugiere aunque no hayas escrito nada**
  (al hacer clic en el campo ya te muestra opciones), y sigue devolviendo
  hasta 10 resultados ordenados alfabéticamente al tipear.
- **Los borrados de cliente y producto ahora son un modal**, no una
  página aparte. Si el borrado se bloquea porque el registro ya tiene
  ventas asociadas, el listado te lo avisa con un mensaje arriba de la
  tabla.

## Qué cambió en esta vuelta

- **Identidad visual "Comedor A.R.M."**: tema oscuro (fondo `#121212`,
  navbar `#0A0A0A`), acento amarillo `#FFC107`, rojo `#D32F2F` para
  peligro/deuda, verde `#2E7D32` para éxito, tarjetas con esquinas de
  `0.75rem`. Se reskinearon las clases de Bootstrap (`.btn-primary`,
  `.btn-danger`, `.btn-success`, tarjetas, tablas, inputs, modales) desde
  un único bloque de CSS en `base.html`, así que no hubo que tocar clase
  por clase en cada template.
- **Cliente Frecuente**: se crea solo, la primera vez que hace falta (al
  entrar a "Nueva venta"), con teléfono genérico y preferencia de pago
  "Contado" — no depende de que alguien se acuerde de correr un comando.
  Ver `_cliente_frecuente()` en `views.py`. Queda preseleccionado en el
  formulario de venta para cobrar rápido sin cargar datos de un cliente
  puntual; se puede cambiar buscando otro cliente normalmente.
- **Cocina A.R.M. rediseñada**: pantalla de 3 columnas grandes
  (PENDIENTES en rojo, EN PREPARACIÓN en amarillo, LISTOS PARA RETIRAR en
  verde), con botones grandes (`btn-lg`, `py-3`) y texto en `fs-4`/`fs-5`
  pensado para leerse de lejos en una tablet montada en la cocina. Sigue
  actualizándose sola cada 20 segundos (ver el aviso sobre WebSockets en
  la vuelta anterior de este README/las notas del chat: esto no es un
  canal en vivo, es una recarga periódica).
- **Impresión en blanco y negro real**: el `@media print` ahora también
  fuerza texto negro sobre fondo blanco (antes solo sacaba el fondo, pero
  el texto seguía siendo claro — hubiera salido casi ilegible en papel
  con el tema oscuro nuevo).

### Nota sobre `tipo_pago`

`Cliente.tipo_pago` cambió de opciones dos veces en total: primero pasó
de texto libre a compartir las opciones de la venta (Efectivo/Crédito/
Transferencia), y ahora tiene su propio set de opciones
(`PREFERENCIA_PAGO_CHOICES`): **Contado**/Crédito/Transferencia, con
"Contado" como valor por defecto. Si ya migraste con la versión anterior,
esta migración va a pedirte confirmar el cambio de opciones — no hace
falta tocar datos a mano, es solo el `choices` del campo.

### Comando opcional para crear el Cliente Frecuente a mano

No hace falta correrlo (se crea solo), pero si querés sembrarlo como
parte de tu script de despliegue, creá este archivo:

`facturacion/management/__init__.py` (vacío)
`facturacion/management/commands/__init__.py` (vacío)
`facturacion/management/commands/crear_cliente_frecuente.py`:
```python
from django.core.management.base import BaseCommand
from facturacion.models import Cliente

class Command(BaseCommand):
    help = 'Crea (si no existe) el Cliente Frecuente usado por defecto en el mostrador.'

    def handle(self, *args, **options):
        cliente, creado = Cliente.objects.get_or_create(
            nombre='Cliente Frecuente',
            defaults={'telefono': '000-000000', 'tipo_pago': 'CONTADO'},
        )
        if creado:
            self.stdout.write(self.style.SUCCESS('Cliente Frecuente creado.'))
        else:
            self.stdout.write('Cliente Frecuente ya existía, no se hizo nada.')
```
Se corre con `python manage.py crear_cliente_frecuente`.

## Decisiones de diseño que siguen vigentes

- El precio y el total de una venta se calculan siempre en el servidor,
  nunca se confía en lo que manda el navegador.
- `DetalleVenta.precio_unitario` es una foto fija del precio al momento
  de la venta.
- `crear_venta` y `pedido_create` corren dentro de una transacción atómica.
- No se puede borrar un cliente ni un producto que ya tengan ventas
  (`on_delete=PROTECT`).
- La deuda por crédito se valida al cobrar (no admite montos en cero,
  negativos, ni mayores a la deuda actual).
- Los listados de ventas e informes usan `select_related`/`annotate` para
  evitar consultas SQL innecesarias.

## Pendiente / a definir

- El modelo `Producto` no tiene campo de stock.
- Solo hay un nivel de usuario (todos ven y hacen todo). Si más adelante
  necesitás diferenciar cajero / cocina / dueño, Django trae grupos y
  permisos ya integrados — encaja bien con el módulo de Pedidos.
