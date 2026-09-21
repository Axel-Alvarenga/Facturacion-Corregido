from django.db import models
from .cliente import Cliente


class PagoDeuda(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago de Gs. {self.monto} - {self.cliente.nombre}"