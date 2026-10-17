import threading
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone

_thread_locals = threading.local()


def get_current_user():
    """Devuelve el usuario actual de la petición en curso, o None."""
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    """Devuelve la request actual, o None."""
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    """Guarda el usuario y la request actuales en un hilo local
    para que estén disponibles desde señales y otras partes del código."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.user = None
            _thread_locals.request = None
        return response


class CierreAutomaticoSistemaMiddleware:
    """Cierra la sesión automáticamente si:

    1. La hora actual es igual o mayor a `CIERRE_SISTEMA_HORA`, O
    2. La última request fue en un día anterior y ya pasó la hora
       de cierre (para el caso "PC apagada, la prendo al otro día").

    Se saltea:
    - La página de login (para poder loguearse).
    - La página de logout.
    - El endpoint de extensión.
    - Los archivos estáticos y media.
    """

    RUTAS_EXCLUIDAS = [
        '/login/',
        '/logout/',
        '/extender-sesion/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo chequear si el usuario está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            if self._debe_cerrar_sesion(request):
                logout(request)
                messages.warning(
                    request,
                    'El sistema está cerrado. Volvé a partir de las '
                    f'{settings.APERTURA_SISTEMA_HORA}:00 hs.'
                )
                return redirect('login')

            # Guardar timestamp de la última request en la sesión
            request.session['ultima_actividad'] = timezone.now().isoformat()

        response = self.get_response(request)
        return response

    def _debe_cerrar_sesion(self, request):
        """Devuelve True si hay que cerrar la sesión."""
        path = request.path_info

        # Saltear rutas excluidas
        for ruta in self.RUTAS_EXCLUIDAS:
            if path.startswith(ruta):
                return False

        # Saltear archivos estáticos y media
        if path.startswith('/static/') or path.startswith('/media/'):
            return False

        # Verificar si hay una extensión activa
        extension_hasta_str = request.session.get('extension_hasta')
        if extension_hasta_str:
            try:
                extension_hasta = datetime.fromisoformat(extension_hasta_str)
                if timezone.is_naive(extension_hasta):
                    extension_hasta = timezone.make_aware(extension_hasta)
                if timezone.now() < extension_hasta:
                    return False
            except (ValueError, TypeError):
                request.session.pop('extension_hasta', None)

        ahora = timezone.localtime()
        hora_cierre = settings.CIERRE_SISTEMA_HORA
        hora_apertura = settings.APERTURA_SISTEMA_HORA

        # Caso 1: estamos en el mismo día y ya pasó la hora de cierre
        if ahora.hour >= hora_cierre:
            return True

        # Caso 2: estamos antes de la hora de apertura (madrugada)
        if ahora.hour < hora_apertura:
            ultima_str = request.session.get('ultima_actividad')
            if ultima_str:
                try:
                    ultima = datetime.fromisoformat(ultima_str)
                    if timezone.is_naive(ultima):
                        ultima = timezone.make_aware(ultima)
                    return True
                except (ValueError, TypeError):
                    return False

        # Caso 3: día distinto al de la última actividad
        ultima_str = request.session.get('ultima_actividad')
        if ultima_str:
            try:
                ultima = datetime.fromisoformat(ultima_str)
                if timezone.is_naive(ultima):
                    ultima = timezone.make_aware(ultima)
                if ultima.date() < ahora.date():
                    if ultima.hour < hora_cierre and ahora.hour >= hora_cierre:
                        return True
                    if ahora.hour < hora_apertura:
                        return True
            except (ValueError, TypeError):
                return False

        return False