from soleadify_ml.models.website_contact import WebsiteContact
import spacy
from django.conf import settings
from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.models.website import Website
from soleadify_ml.models.website_meta import WebsiteMeta
from soleadify_ml.utils.SpiderUtils import get_possible_email


class Command(BaseCommand):
    soc_spacy = None
    spacy_model = None
    help = "Add to queue"
    cached_persons = {}
    cached_organizations = {}

    def handle(self, *args, **options):
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)

        while True:

            websites = Website.objects.raw("select foo.id  from "
                                           "(select distinct wm.website_id as id from website_metas wm "
                                           "JOIN website_metas wm2 ON wm2.website_id = wm.website_id "
                                           "where wm.meta_key='EMAIL' and wm2.meta_key='ORG') foo "
                                           "left JOIN website_contacts wc ON wc.website_id = foo.id "
                                           "and (8 & wc.score) "
                                           "where wc.website_id is null")
            if len(websites) <= 0:
                break
            progress_bar = tqdm(desc="Processing", total=len(websites))
            for website in websites:
                website_metas = WebsiteMeta.objects. \
                    values_list('website_id', 'meta_key', 'meta_value'). \
                    filter(meta_key__in=['EMAIL', 'ORG']). \
                    filter(website_id=website.id)

                for website_meta in website_metas:
                    if website_meta[1] == 'ORG':
                        doc = self.spacy_model(website_meta[2])
                        person = None

                        for ent in doc.ents:
                            if ent.label_ == 'PERSON':
                                person = ent.text

                        if person:
                            for website_meta_v2 in website_metas:
                                if website_meta_v2[1] == 'EMAIL':
                                    match_email = get_possible_email(person, website_meta_v2[2])

                                    if match_email:
                                        contact = {"PERSON": person, "EMAIL": [website_meta_v2[2]], 'URL': None}
                                        WebsiteContact.save_contact(website, contact, 64)
                                        print("person: %, email: %", person, website_meta_v2[2])
                                        break

                    progress_bar.update(1)

            progress_bar.close()
