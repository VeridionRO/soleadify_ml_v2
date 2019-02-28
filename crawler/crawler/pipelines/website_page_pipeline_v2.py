import logging
import json

from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element

logger = logging.getLogger('soleadify_ml')


class WebsitePagePipelineV2(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        try:
            response = item['response']
            text = get_text_from_element(response.text)
            doc = spider.spacy_model(text)
            person_names = []

            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    person_names.append(ent.text)
                    continue

            for person_name in person_names:
                person_elements = response.xpath('//*[contains(text(),"%s")]' % person_name)
                for person_element in person_elements:
                    person = get_person_from_element(spider.spacy_model, person_element.root)
                    if person and WebsiteContact.valid_contact(person):
                        logger.debug(json.dumps(person))
                        WebsiteContact.add_contact(person, spider.contacts, spider.emails, False)
        except AttributeError as exc:
            logger.error(str(exc))
            pass

        return item
