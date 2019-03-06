import json
import logging
from datetime import time
import time
from lxml import etree
import functools
import html2text
import re
import hashlib

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
    converter.emphasis_mark = ' '

    page_text = converter.handle(element_html)

    page_text = page_text.replace('(mailto:', ' ')
    page_text = page_text.replace('mailto:', ' ')
    page_text = re.sub(r'[^a-zA-Z0-9@\- ,.:\n&()_\'|]+', ' ', page_text)
    page_text = re.sub(r'(\s*\n\s*)+', '\n', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)

    return page_text


def get_person_from_element(spider, person_name, dom_element, previous_person=None, depth=1, page=''):
    global added_time
    element_html = etree.tostring(dom_element).decode("utf-8")
    dom_element_text = get_text_from_element(element_html)
    dom_element_text_key = hashlib.md5(dom_element_text.encode()).hexdigest()
    docs = []
    t1 = time.time()

    try:
        if dom_element_text_key in spider.cached_docs:
            docs = spider.cached_docs[dom_element_text_key]
        else:
            spider.soc_spacy.sendall(dom_element_text.encode('utf8') + '--end--'.encode('utf8'))
            docs = json.loads(recv_end(spider.soc_spacy))
            new_docs = {}

            for doc in docs:
                doc_key_text = doc['label'] + doc['text']
                doc_key = hashlib.md5(doc_key_text.encode()).hexdigest()
                new_docs[doc_key] = doc

            docs = new_docs.values()

            spider.cached_docs[dom_element_text_key] = docs
    except:
        logger.error(page + ": error")

    added_time += time.time() - t1
    logger.debug(page + ' - ' + str(added_time))

    person = enough_for_a_person(docs)

    if person and valid_contact(person, 4):
        return person

    if depth > 4:
        return previous_person

    if not person and previous_person:
        return previous_person
    else:
        parent = dom_element.getparent()
        if parent is not None:
            return get_person_from_element(spider, person_name, parent, person, depth + 1, page)


def enough_for_a_person(docs):
    contact = entities_to_contact(docs)

    # this resolves the case when we are on the page of an person and on that page there is mention to another person
    if 'PERSON' in contact and 1 < len(contact['PERSON']) <= 2 and 'EMAIL' in contact and len(contact['EMAIL']) == 1:
        for person_name in contact['PERSON']:
            possible_email = WebsiteContact.get_possible_email(person_name, contact['EMAIL'][0])
            if possible_email:
                contact['PERSON'] = [person_name]
                break

    if valid_contact(contact):
        return contact

    return None


def is_phone_getter(token):
    pattern = re.compile("([\+|\(|\)|\-| |\.|\/]*[0-9]{1,9}[\+|\(|\)|\-| |\.|\/]*){7,}")
    if pattern.match(token.text):
        return True
    else:
        return False


def get_ent(current_entity):
    text = current_entity.text
    if len(text) <= 2:
        return None

    if current_entity.label_ == 'ORG':
        return None

    if current_entity.label_ == 'EMAIL':
        if not current_entity.root.like_email:
            return None

    if current_entity.label_ == 'PHONE':
        text = re.sub('\D', '', text)
        if not current_entity._.get('is_phone'):
            return None

        if len(text) <= 7:
            return None

    return {'label': current_entity.label_, 'text': text.strip(), 'start': current_entity.start,
            'end': current_entity.end}


def title_except(s):
    exceptions = ['a', 'an', 'of', 'the', 'is']
    word_list = re.split(' ', s)  # re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


def valid_contact(contact, length=1):
    """
    check if a contact array is valid
    :param contact:
    :param length:
    :return:
    """
    important_keys = ['PERSON', 'TITLE', 'EMAIL', 'PHONE']
    contact_keys = contact.keys()
    important_keys_intersection = list(set(important_keys) & set(contact_keys))

    if len(important_keys_intersection) <= length:
        return False

    if 'PERSON' not in contact:
        return False
    else:
        if len(contact['PERSON']) > 1:
            return False

    return True


def process_secondary_contacts(docs):
    current_contact = {}
    secondary_contacts = []
    previous_start = 0
    previous_label = None
    for current_entity in docs:
        label = current_entity['label']
        text = current_entity['text']
        start = current_entity['start']

        if start and current_entity['start'] - previous_start > 50:
            if valid_contact(current_contact):
                secondary_contacts.append(current_contact)
            current_contact = {}

        if label == 'PERSON' and label in current_contact:
            name = current_contact['PERSON'][0][0]
            if name != text and valid_contact(current_contact):
                secondary_contacts.append(current_contact)
                current_contact = {label: [(text, start)]}
            elif name == text:
                current_contact[label] = [(text, start)]
        elif label in current_contact:
            if previous_label != label and valid_contact(current_contact):
                secondary_contacts.append(current_contact)
                current_contact = {label: [(text, start)]}
            else:
                current_contact[label].append((text, start))
        else:
            current_contact[label] = [(text, start)]

        previous_label = current_entity['label']
        previous_start = current_entity['start']
    if current_contact:
        secondary_contacts.append(current_contact)

    return secondary_contacts


def entities_to_contact(entities):
    contact = {}
    for ent in entities:
        ent_text = ent['text']
        ent_label = ent['label']

        if ent_label in ['TITLE', 'PERSON']:
            ent_text = title_except(ent_text)

        if ent['label'] == 'ORG':
            continue

        if ent_label in contact:
            if ent_text not in contact[ent_label]:
                contact[ent_label].append(ent_text)
        else:
            contact[ent_label] = [ent_text]

    return contact
