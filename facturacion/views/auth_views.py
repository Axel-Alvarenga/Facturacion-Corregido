from datetime import timedelta
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'facturacion/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def extender_sesion(request):
    """Extiende la sesión por X minutos (configurable en settings).
    Devuelve JSON para que el JS sepa cuándo se cierra de nuevo."""
    minutos = getattr(settings, 'EXTENSION_MINUTOS', 10)
    ahora = timezone.now()
    extension_hasta = ahora + timedelta(minutes=minutos)
    request.session['extension_hasta'] = extension_hasta.isoformat()
    return JsonResponse({
        'ok': True,
        'extension_hasta': extension_hasta.isoformat(),
        'minutos': minutos,
    })