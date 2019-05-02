import logging

from django.core.management.base import BaseCommand
from soleadify_ml.models.website import Website
from soleadify_ml.tasks import get_version

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add to queue"

    def add_arguments(self, parser):
        parser.add_argument('step', type=int)

    def handle(self, *args, **options):
        step = options['step']
        limit = 2000000
        offset = step * 2000000
        websites = Website.objects.raw(
            # "select w.id from websites w limit %s offset %s" % (limit, offset)
            "select w.id from websites w"
        )
        # progress_bar = tqdm(desc="Processing", total=len(websites))
        for website in websites:
            get_version.delay(website.id)
            logger.info(website.id)
            # progress_bar.update(1)
        # progress_bar.close()
