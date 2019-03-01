import logging
from datetime import time
import time
from lxml import etree
import functools
import html2text
import re

from soleadify_ml.models.website_contact import WebsiteContact

t = None
logger = logging.getLogger('soleadify_ml')
added_time = None


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


def get_person_from_element(spacy_model, dom_element, previous_person=None, depth=1):
    global added_time
    element_html = etree.tostring(dom_element).decode("utf-8")
    dom_element_text = get_text_from_element(element_html)

    t1 = time.time()
    doc = spacy_model(dom_element_text)
    added_time += time.time() - t1
    person = enough_for_a_person(doc)

    if person and WebsiteContact.valid_contact(person, 4):
        return person

    if depth > 4:
        return previous_person

    if not person and previous_person:
        logger.debug(added_time)
        return previous_person
    else:
        parent = dom_element.getparent()
        if parent is not None:
            return get_person_from_element(spacy_model, parent, person, depth + 1)


def enough_for_a_person(doc):
    person = {}

    for ent in doc.ents:
        ent_text = ent.text

        if ent.label_ == 'ORG':
            continue

        if ent.label_ == 'EMAIL':
            if not ent.root.like_email:
                continue

        if ent.label_ == 'PHONE':
            if not ent._.get('is_phone'):
                continue
            ent_text = re.sub(r'[^0-9]+', '', ent_text)

        if ent.label_ in person:
            person[ent.label_].append(ent_text)
        else:
            person[ent.label_] = [ent_text]

    if WebsiteContact.valid_contact(person):
        return person

    return None


def is_phone_getter(token):
    pattern = re.compile("([\+|\(|\)|\-| |\.|\/]*[0-9]{1,9}[\+|\(|\)|\-| |\.|\/]*){7,}")
    if pattern.match(token.text):
        return True
    else:
        return False
