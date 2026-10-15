"""
Señales de Django para registrar automáticamente los eventos de auditoría.

Se conectan a los modelos y a las señales de login/logout.
"""
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import (
    RegistroAuditoria,
    Producto, Cliente, Venta, DetalleVenta, ItemVentaManual,
    PagoDeuda, PedidoCocina, DetallePedido,
)
from .middleware import get_current_user, get_current_request


# =========================================================
# Utilidades
# =========================================================
def _get_ip_and_agent():
    """Extrae la IP y el user-agent de la request actual (si existe)."""
    request = get_current_request()
    if not request:
        return None, ''

    # IP (respetando proxies si los hubiera)
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        ip = x_forwarded.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    return ip, user_agent


def _auditar(accion, modelo, obj, cambios=None, metadata=None):
    """Crea un registro de auditoría."""
    usuario = get_current_user()
    ip, ua = _get_ip_and_agent()

    # Si el usuario es anónimo, guardamos None
    if usuario is not None and not getattr(usuario, 'is_authenticated', False):
        usuario = None

    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        modelo=modelo,
        objeto_id=getattr(obj, 'pk', None),
        objeto_repr=str(obj)[:255],
        cambios=cambios or {},
        ip=ip,
        user_agent=ua,
        metadata=metadata or {},
    )


def _diff(instance, campos_excluir=None):
    """Devuelve {campo: [antes, después]} comparando el estado actual
    con el estado en la BD (si es una edición). Solo funciona si la
    instancia ya estaba guardada (pk y no _state.adding)."""
    if instance._state.adding or not instance.pk:
        return {}

    try:
        viejo = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return {}

    diff = {}
    excluir = set(campos_excluir or [])

    for campo in instance._meta.fields:
        nombre = campo.name
        if nombre in excluir:
            continue
        valor_viejo = getattr(viejo, nombre)
        valor_nuevo = getattr(instance, nombre)
        if valor_viejo != valor_nuevo:
            # Intentar serializar a algo JSON-friendly
            diff[nombre] = [_serializar(valor_viejo), _serializar(valor_nuevo)]

    return diff


def _serializar(valor):
    """Convierte un valor a algo que JSONField pueda guardar."""
    if valor is None:
        return None
    if isinstance(valor, (str, int, float, bool)):
        return valor
    if hasattr(valor, 'pk'):
        # Es un modelo relacionado: guardamos su repr
        return str(valor)
    return str(valor)


# =========================================================
# Auditoría genérica con post_save / post_delete
# =========================================================
def _registrar_post_save(sender, instance, created, **kwargs):
    nombre_modelo = sender.__name__

    if created:
        _auditar('CREAR', nombre_modelo, instance)
    else:
        # Solo auditamos si hubo cambios reales
        cambios = _diff(instance)
        if cambios:
            _auditar('EDITAR', nombre_modelo, instance, cambios=cambios)


def _registrar_post_delete(sender, instance, **kwargs):
    nombre_modelo = sender.__name__
    _auditar('ELIMINAR', nombre_modelo, instance)


# =========================================================
# Conectar señales de modelos de negocio
# =========================================================
# Lista de modelos que queremos auditar
MODELOS_A_AUDITAR = [
    Producto,
    Cliente,
    Venta,
    DetalleVenta,
    ItemVentaManual,
    PagoDeuda,
    PedidoCocina,
    DetallePedido,
]

for modelo in MODELOS_A_AUDITAR:
    post_save.connect(_registrar_post_save, sender=modelo)
    post_delete.connect(_registrar_post_delete, sender=modelo)


# =========================================================
# Auditoría de User (crear/editar/eliminar usuarios)
# =========================================================
from django.contrib.auth.models import User


def _registrar_user_post_save(sender, instance, created, **kwargs):
    if created:
        _auditar('CREAR', 'User', instance, metadata={'username': instance.username})
    else:
        cambios = _diff(instance, campos_excluir=['password', 'last_login'])
        if cambios:
            _auditar('EDITAR', 'User', instance, cambios=cambios)


post_save.connect(_registrar_user_post_save, sender=User)


# =========================================================
# Auditoría de login/logout
# =========================================================
@receiver(user_logged_in)
def _registrar_login(sender, request, user, **kwargs):
    ip, ua = _get_ip_and_agent()
    RegistroAuditoria.objects.create(
        usuario=user,
        accion='LOGIN',
        modelo='User',
        objeto_id=user.pk,
        objeto_repr=user.username,
        ip=ip,
        user_agent=ua,
    )


@receiver(user_logged_out)
def _registrar_logout(sender, request, user, **kwargs):
    if user is None:
        return
    ip, ua = _get_ip_and_agent()
    RegistroAuditoria.objects.create(
        usuario=user,
        accion='LOGOUT',
        modelo='User',
        objeto_id=user.pk,
        objeto_repr=user.username,
        ip=ip,
        user_agent=ua,
    )