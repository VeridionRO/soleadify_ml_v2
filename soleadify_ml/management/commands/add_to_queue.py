from tqdm import tqdm
from django.core.management.base import BaseCommand

from soleadify_ml.models.website import Website
from soleadify_ml.tasks import scrapping


class Command(BaseCommand):
    help = "Add to queue"

    def handle(self, *args, **options):
        websites = Website.objects. \
            values_list('id'). \
            filter(contact_state='pending').all()
        progress_bar = tqdm(desc="Processing", total=len(websites))
        for website in websites:
            scrapping.delay(website[0])
            progress_bar.update(1)
        progress_bar.close()
