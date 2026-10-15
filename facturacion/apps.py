from django.apps import AppConfig


class FacturacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'facturacion'
    verbose_name = 'Facturación'

    def ready(self):
        # Importar las señales para que se registren al arrancar Django.
        # El comentario noqa es para que el linter no marque el import
        # como "no usado" (sí se usa: registra las señales por efecto secundario).
        import facturacion.signals  # noqa: F401