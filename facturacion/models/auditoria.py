from django.db import models
from django.conf import settings


class RegistroAuditoria(models.Model):
    """Registro de auditoría de acciones sobre el sistema.
    Se llena automáticamente desde señales de Django."""

    ACCION_CHOICES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('LOGIN_FALLIDO', 'Intento de login fallido'),
    ]

    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_auditoria',
    )
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES, db_index=True)
    modelo = models.CharField(max_length=100, db_index=True)
    objeto_id = models.IntegerField(null=True, blank=True, db_index=True)
    objeto_repr = models.CharField(max_length=255, blank=True)
    cambios = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Registros de auditoría'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['modelo', '-fecha']),
            models.Index(fields=['accion', '-fecha']),
        ]

    def __str__(self):
        quien = self.usuario.username if self.usuario else 'Sistema'
        return f"[{self.fecha:%d/%m/%Y %H:%M}] {quien} {self.accion} {self.modelo} → {self.objeto_repr}"