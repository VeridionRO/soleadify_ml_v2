from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.tasks import splash_website_spider


class Command(BaseCommand):
    help = "Add to queue"

    def handle(self, *args, **options):
        # websites = Website.objects.raw(
        #     "select w.id from websites w "
        # )
        progress_bar = tqdm(desc="Processing", total=1000)
        for i in range(1000):
            # website.contact_state = 'pending'
            # website.save(update_fields=['contact_state'])
            splash_website_spider.delay(i)
            progress_bar.update(1)
        progress_bar.close()
