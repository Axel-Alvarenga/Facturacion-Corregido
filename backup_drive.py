"""
Script para hacer backup de la base de datos y subirlo a Google Drive.
Uso: python backup_drive.py

Flujo:
1. Genera un backup local con django-dbbackup (carpeta backups/)
2. Busca el archivo .sqlite3 más reciente
3. Lo sube a la carpeta "Facturacion_Backups" en tu Google Drive
"""
import os
import sys
import subprocess
from pathlib import Path

from gdrive_core import GDriveCore

# Carpeta local de backups (configurada en settings.py)
BACKUP_DIR = Path(__file__).resolve().parent / 'backups'
NOMBRE_CARPETA_DRIVE = 'Facturacion_Backups'


def generar_backup_local():
    """Ejecuta 'python manage.py dbbackup' y devuelve el archivo más reciente."""
    print('📦 Generando backup local...')
    resultado = subprocess.run(
        [sys.executable, 'manage.py', 'dbbackup'],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        print('❌ Error al generar el backup:')
        print(resultado.stdout)
        print(resultado.stderr)
        sys.exit(1)

    print(resultado.stdout.strip())

    # Buscar el archivo .sqlite3 más reciente
    if not BACKUP_DIR.exists():
        print(f'❌ No existe la carpeta {BACKUP_DIR}')
        sys.exit(1)

    archivos = list(BACKUP_DIR.glob('*.sqlite3'))
    if not archivos:
        print('❌ No se generó ningún archivo .sqlite3')
        sys.exit(1)

    archivo_mas_reciente = max(archivos, key=lambda f: f.stat().st_mtime)
    print(f'✅ Backup local: {archivo_mas_reciente.name}')
    return archivo_mas_reciente


def subir_a_drive(ruta_backup):
    """Sube el archivo a la carpeta de Drive."""
    print('☁️  Conectando a Google Drive...')

    with GDriveCore(
        auth_type='oauth2',
        credentials_file='credentials.json',
        token_file='token.json',
    ) as drive:
        print('📁 Buscando/creando carpeta en Drive...')
        folder_id = drive.get_or_create_folder(NOMBRE_CARPETA_DRIVE)
        print(f'   Carpeta ID: {folder_id}')

        print(f'⬆️  Subiendo {ruta_backup.name}...')
        file_id = drive.upload_file(str(ruta_backup), folder_id=folder_id)
        print(f'✅ Subido a Drive. ID: {file_id}')
        print(f'   Nombre: {ruta_backup.name}')
        return file_id


def main():
    print('=' * 60)
    print('  BACKUP A GOOGLE DRIVE - Comedor A.R.M.')
    print('=' * 60)

    archivo = generar_backup_local()
    subir_a_drive(archivo)

    print('=' * 60)
    print('🎉 Backup completado exitosamente.')
    print('=' * 60)


if __name__ == '__main__':
    main()