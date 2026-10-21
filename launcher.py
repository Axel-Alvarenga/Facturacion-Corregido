import os
import sys

# --- LIMPIAR ENTORNO DE SNAP PARA EVITAR CONFLICTOS CON WEBKIT ---
os.environ.pop("GTK_PATH", None)
os.environ.pop("GIO_MODULE_DIR", None)
os.environ.pop("LD_LIBRARY_PATH", None)
# -----------------------------------------------------------------

# Desactivar aceleración por hardware para evitar el error interno de WebKit
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
    """Verifica si hay actualizaciones y muestra una ventana personalizada."""
    try:
        subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result = subprocess.run(["git", "status", "-uno"], capture_output=True, text=True)
        
        if "behind" in result.stdout.lower() or "detrás" in result.stdout.lower():
            # --- CREAR VENTANA PERSONALIZADA ---
            root = tk.Tk()
            root.title("Actualización Disponible")
            
            # Colores basados en tu sistema
            color_fondo = "#1E1E1E"
            color_texto = "#EAEAEA"
            color_acento = "#FFC107"
            
            root.configure(bg=color_fondo)
            root.geometry("450x300")
            root.resizable(False, False)
            
            # Centrar la ventana en la pantalla
            root.eval('tk::PlaceWindow . center')

            # Intentar cargar el logo
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
                    print("Pillow no instalado. El logo no se mostrará.")

            # Título
            tk.Label(root, text="¡Nueva versión disponible!", font=("Helvetica", 14, "bold"), 
                     fg=color_acento, bg=color_fondo).pack(pady=(5, 5))
            
            # Mensaje
            tk.Label(root, text="Hay cambios nuevos en el sistema.\n¿Querés actualizar y reiniciar ahora?", 
                     font=("Helvetica", 10), fg=color_texto, bg=color_fondo).pack(pady=5)

            # Botones
            frame_botones = tk.Frame(root, bg=color_fondo)
            frame_botones.pack(pady=20)

            def actualizar():
                root.destroy()
                print("Descargando actualización...")
                try:
                    subprocess.run(["git", "pull"], check=True)
                    messagebox.showinfo("Actualización completada", "La aplicación se reiniciará en un momento.")
                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error al actualizar", f"No se pudo actualizar.\nError: {e}")

            def cancelar():
                root.destroy()

            # Botón Actualizar (Amarillo)
            btn_actualizar = tk.Button(frame_botones, text="Actualizar Ahora", command=actualizar,
                                       bg=color_acento, fg="#121212", font=("Helvetica", 10, "bold"),
                                       relief="flat", padx=15, pady=5, cursor="hand2")
            btn_actualizar.pack(side=tk.LEFT, padx=10)

            # Botón Cancelar (Gris)
            btn_cancelar = tk.Button(frame_botones, text="Más tarde", command=cancelar,
                                     bg="#424242", fg="#EAEAEA", font=("Helvetica", 10),
                                     relief="flat", padx=15, pady=5, cursor="hand2")
            btn_cancelar.pack(side=tk.LEFT, padx=10)

            root.mainloop()
            # --- FIN VENTANA PERSONALIZADA ---

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
    
    # --- FORZAR A QUE LOS ENLACES SE ABRAN EN LA MISMA VENTANA (Para PDFs) ---
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False
    # ------------------------------------------------------------------------

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

    # 5. Iniciar PyWebView
    webview.start(icon=icon_path)

if __name__ == '__main__':
    main()