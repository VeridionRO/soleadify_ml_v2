import logging
import json
import re
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element, \
    valid_contact, process_secondary_contacts, pp_contact_name
from soleadify_ml.utils.SocketUtils import recv_end
from scrapy.http import HtmlResponse

logger = logging.getLogger('soleadify_ml')


class WebsitePagePipelineV2(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        response = item['response']
        try:
            logger.debug("start page: " + response.url)
            html = re.sub(r'\s\s+', ' ', response.text)
            new_response = HtmlResponse(url=response.url, body=html, encoding='utf8')
            text = get_text_from_element(html)
            docs = []

            try:
                spider.soc_spacy.sendall(text.encode('utf8') + '--end--'.encode('utf8'))
                docs = json.loads(recv_end(spider.soc_spacy))
            except Exception as ve:
                logger.error(response.url + ": " + ve)

            person_names = []
            has_one_person = False
            has_two_person = False

            for ent in docs:
                if ent['label'] == 'EMAIL':
                    if ent['text'] not in spider.emails:
                        spider.emails.append(ent['text'])
                if ent['label'] == 'ORG':
                    continue
                if ent['label'] == 'PERSON':
                    if has_one_person:
                        if has_two_person:
                            continue
                        has_two_person = True
                    has_one_person = True
                    person_names.append(ent['text'])
                else:
                    has_one_person = False
                    has_two_person = False

            person_names = set(person_names)
            for person_name in person_names:
                name_key = WebsiteContact.get_name_key(person_name)

                if name_key in spider.contacts and spider.contacts[name_key]['DONE']:
                    logger.debug("contact cached: " + json.dumps(spider.contacts[name_key]) + " : " + response.url)
                    continue

                person_elements = new_response.xpath('//*[contains(text(),"%s")]' % person_name)
                for person_element in person_elements:
                    person = get_person_from_element(spider, person_name, person_element.root, page=response.url)
                    if person and valid_contact(person):
                        person['URL'] = response.url
                        logger.debug(json.dumps(person))
                        new_contact = WebsiteContact.add_contact(person, spider.contacts, spider, False)

                        if new_contact['DONE']:
                            break
            logger.debug("end page: " + response.url)

            secondary_contacts = process_secondary_contacts(docs)

            for secondary_contact in secondary_contacts:
                if valid_contact(secondary_contact, has_contact=True):
                    secondary_contact['URL'] = response.url
                    WebsiteContact.add_contact(secondary_contact, spider.secondary_contacts, spider)

        except AttributeError as exc:
            logger.error("pipeline error: " + response.url + '-' + str(exc))
            pass

        return item
