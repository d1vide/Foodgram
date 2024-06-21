import csv
import os

from django.core.management.base import BaseCommand
from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    help = 'Load ingredients into the database'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'data',
                                 'ingredients.csv')
        if not os.path.exists(file_path):
            return
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=measurement_unit.strip()
                )
