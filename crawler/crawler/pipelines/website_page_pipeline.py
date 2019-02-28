import spacy
import re
from django.conf import settings
from spacy.tokens.span import Span
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline


class WebsitePagePipeline(object):
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
        doc = self.spacy_model(item['text'])
        current_entities = []

        for ent in doc.ents:
            ent_text = ent.text

            if ent.label_ == 'ORG':
                continue

            if ent.label_ == 'EMAIL':
                if not ent.root.like_email:
                    continue
                spider.emails.append(ent_text)

            if ent.label_ == 'PHONE':
                if not ent._.get('is_phone'):
                    continue
                ent_text = re.sub(r'[^0-9]+', '', ent_text)

            current_entities.append((ent.label_, ent_text, ent.start))

        current_contact = {}
        start = None

        for current_entity in current_entities:
            if start and current_entity[2] - start > 200:
                if WebsiteContact.valid_contact(current_contact):
                    WebsiteContact.add_contact(current_contact, spider.contacts, spider.emails)
                current_contact = {}

            label = current_entity[0]
            text = current_entity[1]
            start = current_entity[2]

            if label == 'PERSON' and label in current_contact:
                name = current_contact['PERSON'][0][0]
                if name != text and WebsiteContact.valid_contact(current_contact):
                    WebsiteContact.add_contact(current_contact, spider.contacts, spider.emails)
                    current_contact = {label: [(text, start)]}
                elif name == text:
                    current_contact[label] = [(text, start)]
            elif label in current_contact:
                last_element = current_contact[label][-1]
                last_element_start = last_element[1]

                if start - last_element_start > 10:
                    current_contact[label] = [(text, start)]
                else:
                    current_contact[label].append((text, start))
            else:
                current_contact[label] = [(text, start)]

        if WebsiteContact.valid_contact(current_contact):
            WebsiteContact.add_contact(current_contact, spider.contacts, spider.emails)

        return item
