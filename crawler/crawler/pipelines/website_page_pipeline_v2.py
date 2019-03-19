import logging
import json
import re

from validate_email import validate_email

from soleadify_ml.management.commands.spacy_server import Command
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline, get_person_from_element, get_text_from_element, \
    valid_contact, pp_contact_name
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
            logger.debug("get names")

            p = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
            regex_emails = re.findall(p, response.text)
            logger.debug("get names")
            valid_regex_emails = set({email for email in regex_emails if validate_email(email)})
            spider.emails.extend(valid_regex_emails)

            person_names = []
            consecutive_persons = 0
            previous_person = None

            for ent in docs:
                if ent['label'] == 'EMAIL':
                    if ent['text'] not in spider.emails:
                        spider.emails.append(ent['text'])
                if ent['label'] in ['ORG', 'LAW_CAT']:
                    spider.website_metas[ent['label']].append(ent['text'])
                    continue
                if ent['label'] == 'PERSON':
                    if ent['text'] != previous_person:
                        consecutive_persons += 1

                        if consecutive_persons < 3 and previous_person:
                            person_names.append(previous_person)

                        previous_person = ent['text']

                else:
                    consecutive_persons = 0

            if previous_person:
                person_names.append(previous_person)

            person_names = set(person_names)
            for person_name in person_names:
                name_parts = WebsiteContact.get_name_key(person_name)
                name_key = name_parts['name_key']

                if name_key in spider.contacts and spider.contacts[name_key]['DONE']:
                    logger.debug("contact cached: %s:%s:", json.dumps(spider.contacts[name_key]), response.url)
                    continue

                person_elements = new_response.xpath('//*[contains(text(),"%s")]' % person_name)
                if len(person_elements) == 0:
                    person_elements = new_response.xpath('//*[contains(.,"%s")]' % person_name)
                    if len(person_elements) > 0:
                        person_elements = [person_elements[-1]]
                    else:
                        pp_name = pp_contact_name({'PERSON': person_name}, True)
                        if 'Surname' in pp_name:
                            pass
                            if 'GivenName' in pp_name:
                                xpath = '//*[contains(.,"%s") and contains(.,"%s")]' % \
                                        (pp_name['Surname'], pp_name['GivenName'])
                                person_elements = new_response.xpath(xpath)
                                if len(person_elements) > 0:
                                    person_elements = [person_elements[-1]]

                for person_element in person_elements:
                    logger.debug("%s - processing names: %s", response.url, person_name)
                    person = get_person_from_element(spider, person_name, person_element.root, page=response.url)
                    if person and valid_contact(person):
                        person['URL'] = response.url
                        logger.debug(json.dumps(person))
                        new_contact = WebsiteContact.add_contact(person, spider.contacts, spider, False)

                        if new_contact['DONE']:
                            break
            logger.debug("end page: %s", response.url)

        except AttributeError as exc:
            logger.error("pipeline error: %s - %s", response.url, str(exc))
            pass

        return item
