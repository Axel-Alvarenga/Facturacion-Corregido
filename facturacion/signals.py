"""
Señales de Django para registrar automáticamente los eventos de auditoría.

Se conectan a los modelos y a las señales de login/logout.

Nota sobre el diff:
- `post_save` se ejecuta DESPUÉS del UPDATE en la BD, así que leer la BD
  en `post_save` devuelve el estado nuevo, no el viejo.
- Por eso usamos `pre_save` para capturar el estado viejo y guardarlo en
  `instance._estado_viejo`. Luego en `post_save` comparamos contra eso.
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed,
)
from django.dispatch import receiver

from .models import (
    RegistroAuditoria,
    Producto, Cliente, Venta, DetalleVenta, ItemVentaManual,
    PagoDeuda, PedidoCocina, DetallePedido,
    Caja, MovimientoCaja,
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


def _serializar(valor):
    """Convierte un valor a algo que JSONField pueda guardar."""
    if valor is None:
        return None
    if isinstance(valor, (str, int, float, bool)):
        return valor
    if hasattr(valor, 'pk'):
        return str(valor)
    return str(valor)


def _snapshot(instance):
    """Devuelve un dict {campo: valor_serializado} con el estado actual
    de todos los campos del modelo."""
    snapshot = {}
    for campo in instance._meta.fields:
        nombre = campo.name
        try:
            valor = getattr(instance, nombre)
            snapshot[nombre] = _serializar(valor)
        except Exception:
            snapshot[nombre] = None
    return snapshot


def _diff_contra_snapshot(instance, snapshot_viejo, campos_excluir=None):
    """Compara el estado actual de la instancia contra un snapshot viejo
    y devuelve {campo: [antes, después]} solo con los campos que cambiaron."""
    if not snapshot_viejo:
        return {}

    excluir = set(campos_excluir or [])
    diff = {}

    for campo in instance._meta.fields:
        nombre = campo.name
        if nombre in excluir:
            continue
        try:
            valor_nuevo = _serializar(getattr(instance, nombre))
        except Exception:
            continue
        valor_viejo = snapshot_viejo.get(nombre)
        if valor_viejo != valor_nuevo:
            diff[nombre] = [valor_viejo, valor_nuevo]

    return diff


# =========================================================
# pre_save: guardar el estado viejo en la instancia
# =========================================================
def _capturar_estado_viejo(sender, instance, **kwargs):
    """Antes de guardar, leemos el estado actual de la BD y lo guardamos
    en `instance._estado_viejo`. Si la instancia es nueva, queda en None."""
    if instance._state.adding or not instance.pk:
        instance._estado_viejo = None
        return

    try:
        viejo = sender.objects.get(pk=instance.pk)
        instance._estado_viejo = _snapshot(viejo)
    except sender.DoesNotExist:
        instance._estado_viejo = None


# =========================================================
# post_save: crear el registro de auditoría
# =========================================================
def _registrar_post_save(sender, instance, created, **kwargs):
    nombre_modelo = sender.__name__

    if created:
        _auditar('CREAR', nombre_modelo, instance)
    else:
        snapshot_viejo = getattr(instance, '_estado_viejo', None)
        cambios = _diff_contra_snapshot(instance, snapshot_viejo)
        if cambios:
            _auditar('EDITAR', nombre_modelo, instance, cambios=cambios)


def _registrar_post_delete(sender, instance, **kwargs):
    nombre_modelo = sender.__name__
    _auditar('ELIMINAR', nombre_modelo, instance)


# =========================================================
# Conectar señales de modelos de negocio
# =========================================================
MODELOS_A_AUDITAR = [
    Producto,
    Cliente,
    Venta,
    DetalleVenta,
    ItemVentaManual,
    PagoDeuda,
    PedidoCocina,
    DetallePedido,
    Caja,
    MovimientoCaja,
]

for modelo in MODELOS_A_AUDITAR:
    pre_save.connect(_capturar_estado_viejo, sender=modelo)
    post_save.connect(_registrar_post_save, sender=modelo)
    post_delete.connect(_registrar_post_delete, sender=modelo)


# =========================================================
# Auditoría de User (crear/editar/eliminar usuarios)
# =========================================================
from django.contrib.auth.models import User


def _capturar_estado_viejo_user(sender, instance, **kwargs):
    _capturar_estado_viejo(sender, instance, **kwargs)


def _registrar_user_post_save(sender, instance, created, **kwargs):
    if created:
        _auditar('CREAR', 'User', instance, metadata={'username': instance.username})
    else:
        snapshot_viejo = getattr(instance, '_estado_viejo', None)
        cambios = _diff_contra_snapshot(
            instance, snapshot_viejo,
            campos_excluir=['password', 'last_login'],
        )
        if cambios:
            _auditar('EDITAR', 'User', instance, cambios=cambios)


pre_save.connect(_capturar_estado_viejo_user, sender=User)
post_save.connect(_registrar_user_post_save, sender=User)


# =========================================================
# Auditoría de login / logout / intentos fallidos
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


@receiver(user_login_failed)
def _registrar_login_fallido(sender, credentials, request=None, **kwargs):
    """Registra intentos fallidos de login. El usuario puede ser None
    (si el username no existe), así que lo guardamos en metadata."""
    ip, ua = _get_ip_and_agent()
    username = credentials.get('username', '') if credentials else ''

    RegistroAuditoria.objects.create(
        usuario=None,
        accion='LOGIN_FALLIDO',
        modelo='User',
        objeto_id=None,
        objeto_repr=username or '(sin username)',
        ip=ip,
        user_agent=ua,
        metadata={'username_intentado': username},
    )