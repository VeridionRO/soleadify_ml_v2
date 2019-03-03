from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.models.category_website import CategoryWebsite
from soleadify_ml.tasks import scrapping


class Command(BaseCommand):
    help = "Add to queue"

    def handle(self, *args, **options):
        categories = CategoryWebsite.objects.values('website_id').filter(category_id__in=[10506, 10511]).all()
        progress_bar = tqdm(desc="Processing", total=len(categories))
        for category in categories:
            scrapping.delay(category['website_id'])
            progress_bar.update(1)
        progress_bar.close()
