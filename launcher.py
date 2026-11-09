import os
import sys
import time

# --- CONFIGURACIÓN MULTIPLATAFORMA DE ZONA HORARIA ---
if os.name != 'nt':  # Si NO es Windows (es decir, es Linux)
    os.environ['TZ'] = 'America/Asuncion'
    try:
        time.tzset()  # Actualiza la zona horaria del proceso en Linux
    except AttributeError:
        pass
    
    # --- LIMPIAR ENTORNO DE SNAP PARA EVITAR CONFLICTOS CON WEBKIT ---
    os.environ.pop("GTK_PATH", None)
    os.environ.pop("GIO_MODULE_DIR", None)
    os.environ.pop("LD_LIBRARY_PATH", None)
    # Desactivar aceleración por hardware para evitar errores de WebKit
    os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
# -----------------------------------------------------------------

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

def crear_ventana_personalizada(titulo, mensaje, botones):
    root = tk.Tk()
    root.title(titulo)
    
    color_fondo = "#1E1E1E"
    color_texto = "#EAEAEA"
    color_acento = "#FFC107"
    
    root.configure(bg=color_fondo)
    root.geometry("450x320")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')

    logo_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.png')
    if os.path.exists(logo_path):
        try:
            from PIL import Image, ImageTk
            img = Image.open(logo_path)
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl_logo = tk.Label(root, image=photo, bg=color_fondo)
            lbl_logo.image = photo 
            lbl_logo.pack(pady=10)
        except ImportError:
            pass

    tk.Label(root, text=titulo, font=("Helvetica", 14, "bold"), 
             fg=color_acento, bg=color_fondo).pack(pady=(5, 5))
    tk.Label(root, text=mensaje, font=("Helvetica", 10), 
             fg=color_texto, bg=color_fondo, justify="center").pack(pady=5)

    frame_botones = tk.Frame(root, bg=color_fondo)
    frame_botones.pack(pady=20)

    for texto, accion, color_bg, color_fg in botones:
        btn = tk.Button(frame_botones, text=texto, command=accion,
                        bg=color_bg, fg=color_fg, font=("Helvetica", 10, "bold"),
                        relief="flat", padx=15, pady=5, cursor="hand2")
        btn.pack(side=tk.LEFT, padx=10)

    root.mainloop()

def check_updates():
    try:
        subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True)
        
        if "behind" in result.stdout.lower() or "detrás" in result.stdout.lower():
            
            def actualizar():
                print("Descargando actualización...")
                try:
                    subprocess.run(["git", "pull"], check=True)
                    
                    crear_ventana_personalizada(
                        "¡Actualización Exitosa!",
                        "Los cambios se descargaron correctamente.\nLa aplicación se reiniciará en un momento.",
                        [("Aceptar", lambda: os._exit(0), "#FFC107", "#121212")]
                    )
                    
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error al actualizar", f"No se pudo actualizar.\nError: {e}")

            def cancelar():
                try:
                    root = tk._default_root
                    if root:
                        root.destroy()
                except Exception:
                    pass

            crear_ventana_personalizada(
                "Actualización Disponible",
                "Hay una nueva versión del sistema en GitHub.\n¿Querés descargarla y reiniciar la aplicación ahora?",
                [
                    ("Actualizar Ahora", actualizar, "#FFC107", "#121212"),
                    ("Más tarde", cancelar, "#424242", "#EAEAEA")
                ]
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
            # Buscamos el archivo en TODAS las carpetas de estáticos posibles
            rutas_posibles = []
            
            # 1. Carpetas de STATICFILES_DIRS (desarrollo)
            for static_dir in settings.STATICFILES_DIRS:
                rutas_posibles.append(os.path.join(static_dir, path.replace('/static/', '')))
            
            # 2. Carpeta STATIC_ROOT (producción / collectstatic)
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                rutas_posibles.append(os.path.join(settings.STATIC_ROOT, path.replace('/static/', '')))
            
            # 3. Carpeta por defecto del proyecto
            rutas_posibles.append(os.path.join(settings.BASE_DIR, path.lstrip('/')))

            # Probamos todas las rutas hasta encontrar el archivo
            for static_file_path in rutas_posibles:
                if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
                    try:
                        with open(static_file_path, 'rb') as f:
                            content = f.read()
                        content_type = mimetypes.guess_type(static_file_path)[0] or 'application/octet-stream'
                        start_response('200 OK', [('Content-Type', content_type)])
                        return [content]
                    except Exception as e:
                        print(f"Error leyendo estático {static_file_path}: {e}")
                        
        # Si no es un estático o no se encontró, pasar a Django
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

    def open_downloads_folder(self):
        """Abre la carpeta de Descargas del sistema operativo (Windows o Linux)."""
        try:
            downloads_path = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_path):
                downloads_path = os.path.expanduser("~/Descargas") 

            if os.name == 'nt':  # Windows
                os.startfile(downloads_path)
            else:  # Linux
                subprocess.Popen(["xdg-open", downloads_path])
        except Exception as e:
            print(f"Error al abrir carpeta de descargas: {e}")

def main():
    global window

    check_updates()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

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
    
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False

    # --- SELECCIÓN DE ICONO SEGÚN EL SISTEMA OPERATIVO ---
    if os.name == 'nt':  # Windows requiere .ico
        icon_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.ico')
    else:  # Linux acepta .png
        icon_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.png')

    window = webview.create_window(
        title='Comedor A.R.M. - Facturación',
        url=server_url,
        fullscreen=True,
        text_select=True, 
        confirm_close=False,   
        js_api=Api()
    )
    
    window.events.closed += on_closed

    try:
        webview.start(icon=icon_path)
    except Exception as e:
        print(f"Aviso: No se pudo cargar el ícono ({e}). Iniciando sin ícono.")
        webview.start()

if __name__ == '__main__':
    main()