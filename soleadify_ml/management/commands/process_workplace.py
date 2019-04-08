import spacy
from django.conf import settings
from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.models.directory_contact import DirectoryContact


class Command(BaseCommand):
    soc_spacy = None
    spacy_model = None
    help = "Add to queue"
    cached_persons = {}
    cached_organizations = {}

    def handle(self, *args, **options):
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)

        directory_contacts = DirectoryContact.objects.raw("select id, workplace from directory_contact "
                                                          "where organization is null and workplace!='null' "
                                                          'and workplace like \'%% at %%\' '
                                                          "group by workplace "
                                                          "having count(1) > 1 "
                                                          "order by count(1) desc ")

        progress_bar = tqdm(desc="Processing", total=len(directory_contacts))

        for directory_contact in directory_contacts:
            workplace = directory_contact.workplace
            doc = self.spacy_model(workplace)
            title = None
            organization = None

            for ent in doc.ents:
                if ent.label_ == 'TITLE':
                    title = ent.text

                if ent.label_ == 'ORG':
                    organization = ent.text

            if organization:
                print("title=%s, organization=%s" % (title, organization))
                DirectoryContact.objects.filter(
                    workplace=workplace
                ).update(
                    title=title,
                    organization=organization,
                )

            progress_bar.update(1)

        print('done batch')
        progress_bar.close()
