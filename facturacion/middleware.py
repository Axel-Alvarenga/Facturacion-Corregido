import threading


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