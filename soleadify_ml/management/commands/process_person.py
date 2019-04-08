import re
import spacy
from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.models.directory_contact import DirectoryContact
import probablepeople as pp
from django.conf import settings

from soleadify_ml.models.website_contact import WebsiteContact


class Command(BaseCommand):
    soc_spacy = None
    spacy_model = None
    help = "Add to queue"
    cached_persons = {}
    cached_organizations = {}

    def handle(self, *args, **options):
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)

        contacts = WebsiteContact.objects.raw(
            "select * from website_contacts where (last_name is null or first_name is null) and "
            "((64 & score) or (32 & score));"
        )
        progress_bar = tqdm(desc="Processing", total=len(contacts))

        for contact in contacts:
            raw_name = contact.name if contact.name else ''
            # raw_name = re.sub(r'[a-zA-Z]{1}\.\s', '', raw_name)
            # raw_name = re.sub(r"[^a-zA-Z']+", ' ', raw_name)
            # raw_workplace = contact.workplace if contact.workplace else ''
            # name_doc = self.spacy_model(raw_name)
            # workplace_doc = self.spacy_model(raw_workplace)
            first_name = None
            last_name = None
            middle_name = None
            organization = None
            title = None

            # for ent in name_doc.ents:
            #     if ent.label_ == 'PERSON':
            #         person = ent.text
            #         split_name_parts = pp.parse(person, 'person')
            #         for split_name_part in split_name_parts:
            #             partial_name = re.sub(r"[^a-zA-Z-']+", '', split_name_part[0]).lower()
            #             if split_name_part[1] == 'GivenName':
            #                 first_name = partial_name
            #             if split_name_part[1] == 'Surname':
            #                 last_name = partial_name
            #             if split_name_part[1] == 'MiddleName':
            #                 middle_name = partial_name
            #         break

            if not first_name:
                split_name_parts = pp.parse(raw_name, 'person')
                for split_name_part in split_name_parts:
                    partial_name = re.sub(r"[^a-zA-Z-']+", '', split_name_part[0]).lower()
                    if split_name_part[1] == 'GivenName':
                        first_name = partial_name
                    if split_name_part[1] == 'Surname':
                        last_name = partial_name
                    if split_name_part[1] == 'MiddleName':
                        middle_name = partial_name

            # for ent in workplace_doc.ents:
            #     if ent.label_ == 'ORG' and not organization:
            #         organization = ent.text
            #     if ent.label_ == 'TITLE' and not title:
            #         title = ent.text

            if (first_name and last_name) or organization or title:
                print("raw_name=%s, first_name=%s, last_name=%s, title=%s, org=%s" %
                      ('', first_name, last_name, title, organization))
                WebsiteContact.objects.filter(
                    id=contact.id,
                    # workplace=contact.workplace,
                ).update(
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    # organization=organization,
                    # title=title,
                )

            progress_bar.update(1)

        print('done batch')
        progress_bar.close()
