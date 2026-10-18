"""
Script para descargar el backup más reciente de Google Drive.
Uso: python restore_drive.py

⚠️  IMPORTANTE:
- Este script SOLO descarga el archivo. NO restaura la base de datos.
- Para restaurar, ejecutá después (con el servidor detenido):
    python manage.py dbrestore -I backups/NOMBRE_DEL_ARCHIVO.sqlite3

Flujo:
1. Lista los archivos en la carpeta "Facturacion_Backups" de Drive
2. Ordena por fecha de modificación (el más reciente primero)
3. Descarga el más reciente a la carpeta local backups/
"""
import sys
from pathlib import Path

from gdrive_core import GDriveCore

BACKUP_DIR = Path(__file__).resolve().parent / 'backups'
NOMBRE_CARPETA_DRIVE = 'Facturacion_Backups'


def descargar_ultimo_backup():
    print('☁️  Conectando a Google Drive...')

    with GDriveCore(
        auth_type='oauth2',
        credentials_file='credentials.json',
        token_file='token.json',
    ) as drive:
        print('📁 Buscando carpeta en Drive...')
        folder_id = drive.get_or_create_folder(NOMBRE_CARPETA_DRIVE)
        print(f'   Carpeta ID: {folder_id}')

        print('🔍 Listando backups en Drive...')
        # Listar solo archivos .sqlite3 dentro de la carpeta
        query = f"'{folder_id}' in parents and name contains '.sqlite3' and trashed=false"
        archivos = drive.list_files(query=query)

        if not archivos:
            print('❌ No hay backups en Drive.')
            sys.exit(1)

        # Ordenar por fecha de modificación (más reciente primero)
        archivos.sort(key=lambda f: f.get('modifiedTime', ''), reverse=True)

        print(f'📋 Encontrados {len(archivos)} backup(s):')
        for i, a in enumerate(archivos[:5], 1):
            print(f'   {i}. {a["name"]}  ({a.get("modifiedTime", "?")})')

        backup = archivos[0]
        print(f'\n🎯 Backup más reciente: {backup["name"]}')

        # Asegurar que exista la carpeta local backups/
        BACKUP_DIR.mkdir(exist_ok=True)
        ruta_destino = BACKUP_DIR / backup['name']

        print(f'⬇️  Descargando a {ruta_destino}...')
        drive.download(backup['id'], str(ruta_destino))
        print(f'✅ Descargado: {ruta_destino}')

        return ruta_destino


def main():
    print('=' * 60)
    print('  RESTAURAR DESDE GOOGLE DRIVE - Comedor A.R.M.')
    print('=' * 60)

    archivo = descargar_ultimo_backup()

    print()
    print('=' * 60)
    print('🎉 Backup descargado exitosamente.')
    print('=' * 60)
    print()
    print('📋 Para RESTAURAR la base de datos:')
    print()
    print('  1. Detené el servidor de Django (Ctrl+C)')
    print('  2. Hacé un backup de seguridad de la BD actual:')
    print(f'       cp db.sqlite3 db.sqlite3.antes_de_restaurar')
    print('  3. Ejecutá la restauración:')
    print(f'       python manage.py dbrestore -I {archivo}')
    print('  4. Volvé a arrancar el servidor:')
    print('       python manage.py runserver')
    print()
    print('⚠️  ADVERTENCIA: la restauración REEMPLAZA todos los datos actuales.')
    print()


if __name__ == '__main__':
    main()