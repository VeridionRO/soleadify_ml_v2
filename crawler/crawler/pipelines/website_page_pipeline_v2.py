import logging
import json
import re
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
                    name_key = re.sub(r'[^a-zA-Z]+', '', ent.text).lower()
                    if name_key in spider.contacts and spider.contacts[name_key]['DONE']:
                        continue

                    person_names.append(ent.text)
                    continue

            person_names = set(person_names)
            for person_name in person_names:
                person_elements = response.xpath('//*[contains(text(),"%s")]' % person_name)
                for person_element in person_elements:
                    person = get_person_from_element(spider.spacy_model, person_element.root)
                    if person and WebsiteContact.valid_contact(person):
                        person['URL'] = response.url
                        logger.debug(json.dumps(person))
                        new_contact = WebsiteContact.add_contact(person, spider, False)

                        if new_contact['DONE']:
                            break

        except AttributeError as exc:
            logger.error(str(exc))
            pass

        return item
