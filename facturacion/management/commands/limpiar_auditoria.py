from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from facturacion.models import RegistroAuditoria


class Command(BaseCommand):
    help = (
        'Borra registros de auditoría más viejos que X días. '
        'Por defecto: 365 días (1 año). Usar --dias para cambiar.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=365,
            help='Cantidad de días a conservar (default: 365)',
        )
        parser.add_argument(
            '--solo-login',
            action='store_true',
            help='Solo borrar registros de LOGIN y LOGOUT (más conservador)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar cuántos registros se borrarían, sin borrarlos.',
        )

    def handle(self, *args, **options):
        dias = options['dias']
        solo_login = options['solo_login']
        dry_run = options['dry_run']

        limite = timezone.now() - timedelta(days=dias)

        qs = RegistroAuditoria.objects.filter(fecha__lt=limite)
        if solo_login:
            qs = qs.filter(accion__in=['LOGIN', 'LOGOUT'])

        cantidad = qs.count()

        if cantidad == 0:
            self.stdout.write(self.style.WARNING('No hay registros para borrar.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY-RUN] Se borrarían {cantidad} registros más viejos que {dias} días.'
            ))
            return

        qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f'Se borraron {cantidad} registros más viejos que {dias} días.'
        ))