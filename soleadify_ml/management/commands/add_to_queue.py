from tqdm import tqdm
from django.core.management.base import BaseCommand

from soleadify_ml.models.website import Website
from soleadify_ml.tasks import scrapping


class Command(BaseCommand):
    help = "Add to queue"

    def handle(self, *args, **options):
        websites = Website.objects.raw(
            "select distinct w.id, w.domain from websites w "
            "JOIN website_locations wl on w.id = wl.website_id "
            "JOIN category_websites cw on w.id = cw.website_id "
            "where country_code = 'us' and region_code in ('ca','tx','fl','ny','il') "
            "and category_id IN (10368) and (w.id >= 7910273)"
        )
        progress_bar = tqdm(desc="Processing", total=len(websites))
        for website in websites:
            website.contact_state = 'pending'
            website.save(update_fields=['contact_state'])
            scrapping.delay(website.id)
            progress_bar.update(1)
        progress_bar.close()
