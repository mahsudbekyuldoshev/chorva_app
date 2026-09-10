from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.models import Listing


class Command(BaseCommand):
    help = "Muddati tugagan (expires_at o'tgan) active/pending e'lonlarni 'expired' holatiga o'tkazadi."

    def handle(self, *args, **options):
        updated = Listing.objects.filter(
            status__in=["active", "pending"],
            expires_at__lt=timezone.now(),
        ).update(status="expired")
        self.stdout.write(
            self.style.SUCCESS(f"{updated} ta e'lon muddati tugagani sababli 'expired' holatiga o'tkazildi.")
        )
