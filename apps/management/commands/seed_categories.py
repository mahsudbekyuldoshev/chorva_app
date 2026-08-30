from django.core.management.base import BaseCommand

from apps.models import Category


class Command(BaseCommand):
    help = 'Seeds initial categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name_uz': 'Sigirlar', 'name_ru': 'Коровы', 'name_en': 'Cows'},
            {'name_uz': 'Qo\'ylar', 'name_ru': 'Овцы', 'name_en': 'Sheep'},
            {'name_uz': 'Echkilar', 'name_ru': 'Козы', 'name_en': 'Goats'},
            {'name_uz': 'Otlar', 'name_ru': 'Лошади', 'name_en': 'Horses'},
            {'name_uz': 'Boshqa', 'name_ru': 'Другое', 'name_en': 'Other'},
        ]
        for data in categories:
            Category.objects.get_or_create(name_uz=data['name_uz'], defaults=data)
        self.stdout.write(self.style.SUCCESS('Successfully seeded categories'))
