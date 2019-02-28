import json
import time
from django.conf import settings
from django.core.management.base import BaseCommand
from soleadify_ml.models.category_website_text import CategoryWebsiteText


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        self.stdout.write(str(time.time()), ending='\n')
        self.stdout.write("Generating keywords", ending='\n')

        category_keywords = CategoryWebsiteText.load_keywords()
        with open(settings.CATEGORY_KEYWORDS_FILE, 'w') as outfile:
            json.dump(category_keywords, outfile)

        self.stdout.write("Generated keywords", ending='\n')
        self.stdout.write(str(time.time()), ending='\n')
