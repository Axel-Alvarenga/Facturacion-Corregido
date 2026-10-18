# Flujo de backup entre PCs

## En la PC principal (antes de viajar)
python backup_drive.py

## En la PC de viaje (al llegar)
python restore_drive.py
python manage.py dbrestore -I backups/NOMBRE.sqlite3
python manage.py runserver

## En la PC de viaje (antes de volver)
python backup_drive.py

## En la PC principal (al volver)
python restore_drive.py
python manage.py dbrestore -I backups/NOMBRE.sqlite3