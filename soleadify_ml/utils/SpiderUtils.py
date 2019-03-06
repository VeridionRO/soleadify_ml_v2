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

    page_text = re.sub(r'[^a-zA-Z0-9@\- ,.:\n&()_\'|]+', ' ', page_text)
    page_text = re.sub(r'(\s*\n\s*)+', '\n', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)

    return page_text


def get_person_from_element(spider, dom_element, previous_person=None, depth=1, page=''):
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
            return get_person_from_element(spider, parent, person, depth + 1, page)


def enough_for_a_person(docs):
    person = {}

    for ent in docs:
        ent_text = ent['text']
        ent_label = ent['label']

        if ent_label in ['TITLE', 'PERSON']:
            ent_text = title_except(ent_text)

        if ent['label'] == 'ORG':
            continue

        if ent_label in person:
            if ent_text not in person[ent_label]:
                person[ent_label].append(ent_text)
        else:
            person[ent_label] = [ent_text]

    if valid_contact(person):
        return person

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

    return {'label': current_entity.label_, 'text': text.strip().lower(), 'start': current_entity.start_char,
            'end': current_entity.end_char}


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
