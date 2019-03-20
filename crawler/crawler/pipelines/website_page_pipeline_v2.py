import logging
import json
import re

from validate_email import validate_email

from soleadify_ml.management.commands.spacy_server import Command
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element, \
    valid_contact
from scrapy.http import HtmlResponse

logger = logging.getLogger('soleadify_ml')


class WebsitePagePipelineV2(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        response = item['response']

        try:
            if not spider.is_linked_allowed(response.url):
                return []
        except AttributeError:
            pass

        try:
            logger.debug("start page: %s", response.url)
            html = re.sub(r'\s\s+', ' ', response.text)
            new_response = HtmlResponse(url=response.url, body=html, encoding='utf8')
            text = get_text_from_element(html)
            docs = Command.get_entities(spider, text, response.url)

            logger.debug("%s - get emails", response.url)
            p = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
            regex_emails = re.findall(p, html)
            valid_regex_emails = set({email for email in regex_emails if validate_email(email)})
            spider.website_metas['EMAIL'].update(valid_regex_emails)

            logger.debug("%s - get names", response.url)
            person_names = spider.get_person_names(docs)

            for person_name in person_names:
                if spider.contact_done(person_name, response.url):
                    continue

                person_elements = spider.get_person_dom_elements(new_response, person_name)

                for person_element in person_elements:
                    logger.debug("%s - processing names: %s", response.url, person_name)
                    person = get_person_from_element(spider, person_name, person_element.root, page=response.url)
                    if person and valid_contact(person):
                        person['URL'] = response.url
                        logger.debug(json.dumps(person))
                        WebsiteContact.add_contact(person, spider, False)

                        if spider.contact_done(person_name, response.url):
                            break
            logger.debug("end page: %s", response.url)

        except AttributeError as exc:
            logger.error("pipeline error: %s - %s", response.url, str(exc))
            pass

        return item
