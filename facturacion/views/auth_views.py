from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Detectar si la sesión expiró por inactividad
    if request.GET.get('expirada') == '1':
        messages.warning(
            request,
            'Tu sesión expiró por inactividad. Volvé a iniciar sesión.'
        )

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