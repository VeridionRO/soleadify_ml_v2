import logging
import json
import re
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element
from soleadify_ml.utils.SocketUtils import recv_end
from scrapy.http import HtmlResponse

logger = logging.getLogger('soleadify_ml')


class WebsitePagePipelineV2(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        try:
            response = item['response']
            logger.debug("start page: " + response.url)
            html = re.sub(r'\s\s+', ' ', response.text)
            new_response = HtmlResponse(url=response.url, body=html, encoding='utf8')
            text = get_text_from_element(html)
            docs = []

            try:
                spider.soc_spacy.sendall(text.encode('utf8') + '--params--1'.encode('utf8') + '--end--'.encode('utf8'))
                docs = json.loads(recv_end(spider.soc_spacy))
            except Exception as ve:
                logger.error(response.url + ": " + ve)

            person_names = []
            has_one_person = False
            has_two_person = False

            for ent in docs:
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
                person_elements = new_response.xpath('//*[contains(text(),"%s")]' % person_name)
                for person_element in person_elements:
                    person = get_person_from_element(spider, person_element.root, page=response.url)
                    if person and WebsiteContact.valid_contact(person):
                        person['URL'] = response.url
                        logger.debug(json.dumps(person))
                        new_contact = WebsiteContact.add_contact(person, spider, False)

                        if new_contact['DONE']:
                            break
            logger.debug("end page: " + response.url)

        except AttributeError as exc:
            logger.error(str(exc))
            pass

        return item
