import pymysql
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

pymysql.install_as_MySQLdb()

# 1. Bypass de verificación de versión
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

# 2. Patch global a nivel de la clase de características de MySQL/MariaDB
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False