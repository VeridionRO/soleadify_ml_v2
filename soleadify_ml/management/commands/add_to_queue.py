from tqdm import tqdm
from django.core.management.base import BaseCommand

from soleadify_ml.models.website import Website
from soleadify_ml.tasks import splash_website_spider


class Command(BaseCommand):
    help = "Add to queue"

    def add_arguments(self, parser):
        parser.add_argument('step', type=int)

    def handle(self, *args, **options):
        step = options['step']
        limit = 1000000
        offset = step * 1000000
        print(step)
        websites = Website.objects.raw(
            "select w.id from websites w limit %s offset %s" % (limit, offset)
        )
        progress_bar = tqdm(desc="Processing", total=len(websites))
        for website in websites:
            splash_website_spider.delay(website.id)
            progress_bar.update(1)
        progress_bar.close()
