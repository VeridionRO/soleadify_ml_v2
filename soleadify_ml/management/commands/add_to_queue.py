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
        limit = 2000
        offset = step * 2000
        websites = Website.objects.raw(
            # "select w.id from websites w limit %s offset %s" % (limit, offset)
            "select w.id from websites w "
            "LEFT JOIN website_versions wj on w.id = wj.website_id "
            "where wj.id is null "
        )
        # progress_bar = tqdm(desc="Processing", total=len(websites))
        # website_ids = []
        for website in websites:
            get_version.delay(website.id, False)
            # website_ids.append(website.id)
            # if len(website_ids) > 1000:
            #     get_version.chunks(zip(website_ids, [False] * len(website_ids)), 100).apply_async(queue='version')
            #     website_ids = []
            logger.info(website.id)
            # progress_bar.update(1)
        # progress_bar.close()
