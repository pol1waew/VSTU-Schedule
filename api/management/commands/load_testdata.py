import json
import os

from django.core.management.base import BaseCommand
from api.importers import JSONImporter


class Command(BaseCommand):
    help = "Загружает тестовые данные в базу данных"

    def handle(self, *args, **kwargs):
        datadir = os.path.abspath("testdata")
        for file in os.listdir(datadir):
            if file.endswith(".json"):
                with open(os.path.join(datadir, file), "r", encoding="utf-8") as fd:
                    data = json.load(fd)
                    self.stdout.write(f"Заполнение данных из файла {file}")
                    JSONImporter(data).import_data()
        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно загружены в базу данных"))
