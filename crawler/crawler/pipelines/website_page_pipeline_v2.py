import spacy
import re
from django.conf import settings
from spacy.tokens.span import Span

from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element


class WebsitePagePipelineV2(object):
    spacy_model = None

    def open_spider(self, spider):
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)

        def is_phone_getter(token):
            pattern = re.compile("([\+|\(|\)|\-| |\.|\/]*[0-9]{1,9}[\+|\(|\)|\-| |\.|\/]*){7,}")
            if pattern.match(token.text):
                return True
            else:
                return False

        Span.set_extension('is_phone', getter=is_phone_getter, force=True)

    @check_spider_pipeline
    def process_item(self, item, spider):
        response = item['response']
        text = get_text_from_element(response.text)
        doc = self.spacy_model(text)
        person_names = []
        persons = {}

        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                person_names.append(ent.text)
                continue

        for person_name in person_names:
            person_elements = response.xpath('//*[contains(text(),"%s")]' % person_name)
            for person_element in person_elements:
                person = get_person_from_element(self.spacy_model, person_element.root)
                if person and WebsiteContact.valid_contact(person):
                    WebsiteContact.add_contact(person, spider.contacts, spider.emails, False)

        print(persons)

        return item
