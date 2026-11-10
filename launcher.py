import os
import sys
import time

# --- CONFIGURACIÓN MULTIPLATAFORMA DE ZONA HORARIA ---
if os.name != 'nt':  # Si NO es Windows (es decir, es Linux)
    os.environ['TZ'] = 'America/Asuncion'
    try:
        time.tzset()
    except AttributeError:
        pass
    
    os.environ.pop("GTK_PATH", None)
    os.environ.pop("GIO_MODULE_DIR", None)
    os.environ.pop("LD_LIBRARY_PATH", None)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_facturacion.settings')

def crear_ventana_personalizada(titulo, mensaje, botones):
    root = tk.Tk()
    root.title(titulo)
    
    color_fondo = "#1E1E1E"
    color_texto = "#EAEAEA"
    color_acento = "#FFC107"
    
    root.configure(bg=color_fondo)
    root.geometry("480x340")
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
        local = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        remoto = subprocess.run(["git", "rev-parse", "origin/master"], capture_output=True, text=True).stdout.strip()
        
        if local != remoto and local != "" and remoto != "":
            
            def actualizar():
                print("Descargando actualización...")
                try:
                    subprocess.run(["git", "pull"], check=True)
                    subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], check=True)
                    subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
                    
                    crear_ventana_personalizada(
                        "¡Actualización Exitosa!",
                        "Los cambios se instalaron correctamente.\nLa aplicación se reiniciará en un momento.",
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
    from django.core.wsgi import get_wsgi_application
    from django.conf import settings
    application = get_wsgi_application()

    def static_handler(environ, start_response):
        path = environ['PATH_INFO']
        if path.startswith('/static/'):
            rutas_posibles = []
            for static_dir in settings.STATICFILES_DIRS:
                rutas_posibles.append(os.path.join(static_dir, path.replace('/static/', '')))
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                rutas_posibles.append(os.path.join(settings.STATIC_ROOT, path.replace('/static/', '')))
            rutas_posibles.append(os.path.join(settings.BASE_DIR, path.lstrip('/')))

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
        if window:
            window.destroy()

    def open_downloads_folder(self):
        try:
            downloads_path = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_path):
                downloads_path = os.path.expanduser("~/Descargas") 
            if os.name == 'nt':
                os.startfile(downloads_path)
            else:
                subprocess.Popen(["xdg-open", downloads_path])
        except Exception as e:
            print(f"Error al abrir carpeta de descargas: {e}")

def on_closing():
    """Se ejecuta cuando el usuario intenta cerrar la ventana."""
    respuesta = messagebox.askyesno(
        "Cerrar Aplicación",
        "¿Querés subir un backup a Google Drive antes de cerrar?"
    )
    
    if respuesta:
        # --- VENTANA DE CARGA PERSONALIZADA CON ANIMACIÓN ---
        carga_root = tk.Tk()
        carga_root.title("Backup en proceso")
        carga_root.configure(bg="#1E1E1E")
        carga_root.geometry("350x180")
        carga_root.resizable(False, False)
        carga_root.eval('tk::PlaceWindow . center')

        # Título
        tk.Label(carga_root, text="Subiendo Backup...", font=("Helvetica", 12, "bold"), 
                 fg="#FFC107", bg="#1E1E1E").pack(pady=(20, 5))
        
        # Contenedor para el spinner y el texto
        frame_anim = tk.Frame(carga_root, bg="#1E1E1E")
        frame_anim.pack(expand=True)

        # Área de dibujo del spinner
        canvas = tk.Canvas(frame_anim, width=40, height=40, bg="#1E1E1E", highlightthickness=0)
        canvas.pack(side=tk.LEFT, padx=10)

        # Texto explicativo
        lbl_msg = tk.Label(frame_anim, text="Por favor, no cierres la ventana.\nEsto puede tardar unos segundos.", 
                           font=("Helvetica", 9), fg="#EAEAEA", bg="#1E1E1E", justify="left")
        lbl_msg.pack(side=tk.LEFT)

        # Variables para la animación
        angulo = 0
        animando = True

        def animar():
            nonlocal angulo
            if not animando: return
            canvas.delete("all")
            # Dibujamos un círculo de fondo
            canvas.create_oval(5, 5, 35, 35, outline="#333333", width=4)
            # Dibujamos el arco que gira (color amarillo)
            canvas.create_arc(5, 5, 35, 35, start=angulo, extent=90, outline="#FFC107", width=4, style=tk.ARC)
            angulo = (angulo - 10) % 360 # Restamos para que gire en sentido horario
            carga_root.after(50, animar) # Repetir cada 50ms

        animar() # Iniciar animación

        resultado_backup = {"code": -1, "stderr": ""}

        def ejecutar_backup():
            # Ejecutamos el script en un hilo para que no congele la animación
            try:
                res = subprocess.run(
                    [sys.executable, "backup_drive.py"], 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8', 
                    errors='replace'
                )
                resultado_backup["code"] = res.returncode
                resultado_backup["stderr"] = res.stderr
            except Exception as e:
                resultado_backup["code"] = 1
                resultado_backup["stderr"] = str(e)

        # Iniciamos el backup en segundo plano
        hilo_backup = threading.Thread(target=ejecutar_backup)
        hilo_backup.start()

        def verificar_fin():
            if hilo_backup.is_alive():
                carga_root.after(100, verificar_fin)
            else:
                nonlocal animando
                animando = False
                carga_root.destroy()
                
                if resultado_backup["code"] == 0:
                    messagebox.showinfo("Backup Exitoso", "El backup se subió correctamente a Google Drive.")
                else:
                    error_msg = resultado_backup["stderr"][-500:] if resultado_backup["stderr"] else "Error desconocido"
                    messagebox.showerror("Error de Backup", f"No se pudo subir el backup.\n\nDetalle:\n{error_msg}")

        # Empezamos a revisar si terminó
        verificar_fin()

        # Iniciamos el bucle de la ventana
        carga_root.mainloop()

    return True

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

    if os.name == 'nt':
        icon_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.ico')
    else:
        icon_path = os.path.join(BASE_DIR, 'facturacion', 'static', 'facturacion', 'img', 'logo.png')

    window = webview.create_window(
        title='Comedor A.R.M. - Facturación',
        url=server_url,
        fullscreen=True,
        text_select=True, 
        confirm_close=True,
        js_api=Api()
    )
    
    window.events.closing += on_closing
    window.events.closed += on_closed

    try:
        webview.start(icon=icon_path)
    except Exception as e:
        print(f"Aviso: No se pudo cargar el ícono ({e}). Iniciando sin ícono.")
        webview.start()

if __name__ == '__main__':
    main()