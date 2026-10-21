import os
import sys

# Desactivar aceleración por hardware para evitar el error interno de WebKit
# (Debe ir antes de importar webview)
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"

import time
import threading
import subprocess
import urllib.request
import tkinter as tk
import tkinter.messagebox as messagebox
from waitress import serve
import mimetypes
import webview

# Asegurarnos de que estamos en el directorio del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_facturacion.settings')

def check_updates():
    """Verifica si hay actualizaciones en Git antes de abrir la app."""
    try:
        subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True)
        if "behind" in result.stdout.lower() or "detrás" in result.stdout.lower():
            messagebox.showwarning(
                "Actualización disponible",
                "Hay una nueva versión de la aplicación en GitHub.\n\n"
                "Por favor, abrí Visual Studio Code, hacé 'git pull' y volvé a iniciar la app."
            )
    except Exception as e:
        print(f"No se pudo verificar actualizaciones: {e}")

def start_server():
    """Inicia el servidor Waitress en un hilo separado, sirviendo estáticos."""
    from django.core.wsgi import get_wsgi_application
    from django.conf import settings

    application = get_wsgi_application()

    def static_handler(environ, start_response):
        path = environ['PATH_INFO']
        if path.startswith('/static/'):
            for static_dir in settings.STATICFILES_DIRS:
                static_file_path = os.path.join(static_dir, path.replace('/static/', ''))
                if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
                    try:
                        with open(static_file_path, 'rb') as f:
                            content = f.read()
                        content_type = mimetypes.guess_type(static_file_path)[0] or 'application/octet-stream'
                        start_response('200 OK', [('Content-Type', content_type)])
                        return [content]
                    except Exception as e:
                        print(f"Error leyendo estático {static_file_path}: {e}")
        return application(environ, start_response)

    print("Iniciando servidor local en http://127.0.0.1:8000...")
    serve(static_handler, host='127.0.0.1', port=8000)

def on_closed():
    print("Cerrando la aplicación...")
    os._exit(0)

class Api:
    def toggle_fullscreen(self):
        global window
        if window:
            window.toggle_fullscreen()
            
    def close_app(self):
        on_closed()

def main():
    global window

    # 1. Verificar actualizaciones
    check_updates()

    # 2. Iniciar el servidor en un hilo separado
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 3. ESPERA ACTIVA: Esperar a que el servidor responda
    print("Esperando a que el servidor esté listo...")
    server_url = 'http://127.0.0.1:8000'
    server_ready = False
    
    for _ in range(30):
        try:
            urllib.request.urlopen(server_url, timeout=1)
            server_ready = True
            break
        except Exception:
            time.sleep(1)

    if not server_ready:
        messagebox.showerror("Error", "No se pudo iniciar el servidor. Revisá la terminal.")
        os._exit(1)

    print("¡Servidor listo! Abriendo ventana...")
    
    # RUTA AL ICONO DEL LOGO
    icon_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.png')

    # 4. Crear la ventana
    window = webview.create_window(
        title='Comedor A.R.M. - Facturación',
        url=server_url,
        fullscreen=True,
        text_select=True, 
        confirm_close=False,   
        js_api=Api()
    )
    
    window.events.closed += on_closed

    # 5. Iniciar PyWebView pasando el ícono en el start()
    webview.start(icon=icon_path)

if __name__ == '__main__':
    main()