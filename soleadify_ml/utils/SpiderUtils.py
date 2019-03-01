import json
import logging
from datetime import time
import time
from lxml import etree
import functools
import html2text
import re

from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SocketUtils import recv_end

logger = logging.getLogger('soleadify_ml')
added_time = 0


def check_spider_pipeline(process_item_method):
    @functools.wraps(process_item_method)
    def wrapper(self, item, spider):
        # if class is in the spider's pipeline, then use the
        # process_item method normally.
        if self.__class__ in spider.pipeline:
            return process_item_method(self, item, spider)

        # otherwise, just return the untouched item (skip this step in
        # the pipeline)
        else:
            return item

    return wrapper


def get_text_from_element(element_html):
    converter = html2text.HTML2Text(bodywidth=0)
    converter.ignore_images = True
    converter.single_line_break = True

    page_text = converter.handle(element_html)

    page_text = re.sub(r'[^a-zA-Z0-9@\- ,.:\n&()\']+', ' ', page_text)
    page_text = re.sub(r'(\s*\n\s*)+', '\n', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)

    return page_text


def get_person_from_element(spider, dom_element, previous_person=None, depth=1, page=''):
    global added_time
    element_html = etree.tostring(dom_element).decode("utf-8")
    dom_element_text = get_text_from_element(element_html)
    docs = []

    t1 = time.time()

    try:
        spider.soc_spacy.sendall(dom_element_text.encode('utf8') + '--end--'.encode('utf8'))
        docs = json.loads(recv_end(spider.soc_spacy))
    except:
        logger.error(page + "error")

    added_time += time.time() - t1
    logger.debug(page + ' - ' + str(added_time))

    person = enough_for_a_person(docs)

    if person and WebsiteContact.valid_contact(person, 4):
        return person

    if depth > 3:
        return previous_person

    if not person and previous_person:
        return previous_person
    else:
        parent = dom_element.getparent()
        if parent is not None:
            return get_person_from_element(spider, parent, person, depth + 1, page)


def enough_for_a_person(docs):
    person = {}

    for ent in docs:
        ent_text = ent['text']

        if ent['label'] == 'ORG':
            continue

        if ent['label'] in person:
            person[ent['label']].append(ent_text)
        else:
            person[ent['label']] = [ent_text]

    if WebsiteContact.valid_contact(person):
        return person

    return None


def is_phone_getter(token):
    pattern = re.compile("([\+|\(|\)|\-| |\.|\/]*[0-9]{1,9}[\+|\(|\)|\-| |\.|\/]*){7,}")
    if pattern.match(token.text):
        return True
    else:
        return False
