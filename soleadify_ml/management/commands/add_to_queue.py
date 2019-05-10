import logging

from django.core.management.base import BaseCommand
from soleadify_ml.models.website import Website
from soleadify_ml.tasks import website_spider

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
            "select distinct w.id, w.domain from category_websites cw "
            "JOIN website_locations wl ON wl.website_id = cw.website_id "
            "JOIN websites w on wl.website_id = w.id "
            "left join website_contacts wc ON wc.website_id = cw.website_id "
            "left join website_metas wm ON wm.website_id = cw.website_id "
            "where category_id=10368 and wl.country_name='united states' and wc.id is null and wm.id is null"
        )
        # progress_bar = tqdm(desc="Processing", total=len(websites))
        # website_ids = []
        for website in websites:
            website_spider.delay(website.id)
