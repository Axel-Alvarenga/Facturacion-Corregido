# 🍳 Comedor A.R.M. — Sistema de Facturación

Sistema de facturación y gestión para un local gastronómico. Desarrollado con **Django** y **SQLite**, con interfaz responsive y tema oscuro.

---

## 📋 Funcionalidades

### 🛒 Ventas
- **Nueva venta** con carrito (productos + ítems manuales).
- **Formas de pago**: Efectivo, Crédito, Transferencia.
- **Cálculo automático** del total, vuelto y monto pagado.
- **Transferencias pendientes**: quedan como `PENDIENTE` hasta que se confirman.
- **Ticket imprimible** (80mm) por venta.
- **Anulación de ventas** (borrado lógico) con motivo y auditoría.
- **Modal de detalle** con productos, ítems manuales, totales y botón de anular.

### 👥 Clientes
- ABM de clientes con validación de duplicados.
- Preferencia de pago: Contado / Crédito / Transferencia.
- **Frecuencia de pago** para clientes con crédito (semanal/mensual).
- **Deuda actual** con saldo a favor permitido (solo clientes crédito).
- **Pago de deuda** con **FIFO** (se aplica a las ventas más viejas primero).
- **Forma de pago** en cada pago (efectivo/transferencia).
- **PDF de deuda por cliente** con historial de ventas a crédito.

### 📦 Productos
- ABM de productos con foto opcional.
- Búsqueda con autocompletado.

### 🍽️ Pedidos de Cocina
- Creación de pedidos con productos.
- Estados: Pendiente → En preparación → Listo → Entregado.
- Vista tipo pizarra que se actualiza cada 20 segundos.

### 💰 Caja
- **Apertura** con monto inicial.
- **Cierre** con monto real contado y cálculo de diferencia.
- **Ingresos y retiros manuales** con descripción.
- **Movimientos automáticos** desde ventas en efectivo y pagos de deuda.
- **Anulación de ventas** marca el movimiento como anulado (no resta del esperado).
- **Tarjeta destacada en dashboard** con estado actual.
- **Badge en navbar** con estado (abierta/cerrada).

### 📊 Informes
- **Pestaña de Ventas**:
  - KPIs: Ventas encontradas, Cobrado, Pendiente, Ticket promedio.
  - Resumen por forma de pago con cobrado vs pendiente.
  - Filtros por cliente, forma de pago, fecha.
  - Exportar a Excel.
  - Imprimir.
- **Pestaña de Deudas**:
  - KPIs: Clientes registrados, Clientes con deuda, Monto total adeudado.
  - Filtros por nombre/local/teléfono + switch "solo con deuda".
  - Botón "Pagar" con `?next=` para volver al informe.
  - Descargar PDF con desglose por cliente.
  - Descargar PDF individual por cliente.

### 🔒 Auditoría
- Registro automático de **CREAR / EDITAR / ELIMINAR** de todos los modelos.
- **Diff real** de los cambios (antes/después).
- **LOGIN / LOGOUT / LOGIN_FALLIDO**.
- Filtros por usuario, acción, modelo, fecha, texto.
- Exportar a Excel.
- Solo visible para superusuarios.

### 💾 Backup a Google Drive
- `backup_drive.py`: genera backup local y lo sube a Drive.
- `restore_drive.py`: descarga el backup más reciente de Drive.
- **Uso pensado** para mover datos entre PC principal y PC de viaje.

### ⏰ Cierre automático
- El sistema se cierra a la hora configurada (`CIERRE_SISTEMA_HORA = 20`).
- Aviso X minutos antes (`AVISO_CIERRE_MINUTOS_ANTES = 5`).
- Botón "Extender 10 minutos" (`EXTENSION_MINUTOS = 10`).
- La extensión respeta el estado al navegar entre módulos.

### 🔐 Autenticación
- Login / Logout.
- Sesión con cierre automático por horario.

---

## 🚀 Instalación

### Requisitos
- Python 3.10+
- pip
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Axel-Alvarenga/Facturacion-Corregido.git
cd Facturacion-Corregido

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env con las variables de entorno
cat > .env << 'EOF'
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Recolectar estáticos (solo producción)
python manage.py collectstatic --noinput

# 8. Arrancar el servidor
python manage.py runserver