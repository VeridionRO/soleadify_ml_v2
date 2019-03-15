import logging
from datetime import time
import time
import functools
import re
import probablepeople as pp
from soleadify_ml.management.commands.spacy_server import Command
from soleadify_ml.utils.HTML2TextV2 import HTML2TextV2
from email_split import email_split
from lxml import etree

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
    converter = HTML2TextV2(bodywidth=0)
    converter.ignore_images = True
    converter.single_line_break = True
    converter.inheader = True
    converter.get_email_phone = True
    converter.emphasis_mark = ' '

    page_text = converter.handle(element_html)

    page_text = page_text.replace('(mailto:', ' ')
    page_text = page_text.replace('mailto:', ' ')
    page_text = page_text.replace('(tel:', ' ')
    page_text = page_text.replace('tel:', ' ')
    page_text = re.sub(r'[^a-zA-Z0-9@\- ,.:\n&()_\'|]+', ' ', page_text)
    page_text = re.sub(r'(\s*\n\s*)+', '\n', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)
    page_text = re.sub(r'\s\s+', ', ', page_text)
    page_text = re.sub(r',+', ',', page_text)
    page_text = re.sub(r', +', ', ', page_text)

    return page_text.strip()


def get_person_from_element(spider, person_name, dom_element, previous_contact=None, depth=1, page='',
                            previous_no=1, previous_dom_element_text=''):
    global added_time
    element_html = etree.tostring(dom_element).decode("utf-8")
    dom_element_text = get_text_from_element(element_html)
    t1 = time.time()
    required_no = 2
    docs = Command.get_entities(spider, dom_element_text, page)

    added_time += time.time() - t1
    logger.debug(page + ' - ' + str(added_time))

    contact = enough_for_a_person(docs, person_name)

    if contact and previous_contact and 'PERSON' in previous_contact and 'PERSON' in contact and len(
            previous_contact['PERSON']) > 0 and len(previous_contact['PERSON']) < len(contact['PERSON']):
        if valid_contact(previous_contact, required_no):
            return previous_contact
        else:
            return None

    if contact and valid_contact(contact, 4):
        return contact

    if depth > 4 and valid_contact(contact, required_no):
        return contact

    if not valid_contact(contact, required_no) and valid_contact(previous_contact, previous_no):
        return previous_contact
    elif depth > 4:
        return None
    else:
        parent = dom_element.getparent()
        if parent is not None:
            new_depth = depth
            if previous_dom_element_text != dom_element_text:
                new_depth += 1
            previous_no = required_no
            previous_dom_element_text = dom_element_text
            return get_person_from_element(spider, person_name, parent, contact, new_depth, page, previous_no,
                                           previous_dom_element_text)


def enough_for_a_person(docs, contact_name):
    contact = entities_to_contact(docs)

    # this resolves the case when we are on the page of an person and on that page there is mention to another person
    if 'PERSON' in contact and 1 < len(contact['PERSON']) <= 2 and 'EMAIL' in contact and len(contact['EMAIL']) == 1:
        for current_contact_name in contact['PERSON']:
            possible_email = get_possible_email(current_contact_name, contact['EMAIL'][0])
            if possible_email:
                contact['PERSON'] = [current_contact_name]
                contact['EMAIL'] = [contact['EMAIL'][0]]
                break

    if 'PERSON' in contact and len(contact['PERSON']) >= 2:
        new_contact_names = []
        duplicate = False
        for contact_name_2 in contact['PERSON']:
            if contact_name == contact_name_2:
                continue

            name_keys = ['GivenName', 'Surname']
            pp_name = pp_contact_name({'PERSON': contact_name})
            pp_name_2 = pp_contact_name({'PERSON': contact_name_2})

            pp_name_keys = list(set(name_keys) & set(pp_name.keys()))
            pp_name_2_keys = list(set(name_keys) & set(pp_name_2.keys()))

            if len(pp_name_keys) > 1 and len(pp_name_2_keys) > 1 and \
                    pp_name['GivenName'] == pp_name_2['GivenName'] and pp_name['Surname'] == pp_name_2['Surname']:
                new_contact_name = contact_name if len(contact_name) > len(contact_name_2) else contact_name_2
                if new_contact_name not in new_contact_names:
                    new_contact_names.append(contact_name)
                    duplicate = True
            else:
                new_contact_names.append(contact_name_2)
            if not duplicate:
                new_contact_names.append(contact_name)

        if len(new_contact_names) > 0:
            contact['PERSON'] = new_contact_names

    return contact


def title_except(s):
    exceptions = ['a', 'an', 'of', 'the', 'is']
    word_list = re.split(' ', s)  # re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


def valid_contact(contact, length=1, has_contact=False):
    """
    check if a contact array is valid
    :param contact:
    :param length:
    :param has_contact:
    :return:
    """
    if not contact:
        return False

    important_keys = ['PERSON', 'TITLE', 'EMAIL', 'PHONE']
    has_contacts_keys = ['EMAIL', 'PHONE']
    contact_keys = contact.keys()
    important_keys_intersection = list(set(important_keys) & set(contact_keys))

    if has_contact:
        has_contact_keys_intersection = list(set(contact_keys) & set(has_contacts_keys))
        if len(has_contact_keys_intersection) == 0:
            return False

    if len(important_keys_intersection) < length:
        return False

    if 'PERSON' not in contact:
        return False
    else:
        if len(contact['PERSON']) > 1 and not isinstance(contact['PERSON'], str):
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

        if start and current_entity['start'] - previous_start > 10:
            if valid_contact(current_contact, 2):
                secondary_contacts.append(current_contact)
            current_contact = {}

        if label == 'PERSON' and label in current_contact:
            name = current_contact['PERSON'][0][0]
            if name != text and valid_contact(current_contact, 2):
                secondary_contacts.append(current_contact)
                current_contact = {label: [(text, start)]}
            elif name == text:
                current_contact[label] = [(text, start)]
        elif label in current_contact:
            previous_value = current_contact[label][-1][0]
            if previous_label != label and valid_contact(current_contact, 2) and previous_value != text:
                secondary_contacts.append(current_contact)
                if not (label == 'EMAIL' and get_possible_email(current_contact['PERSON'][0][0], text)):
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
    previous_line_number = None
    for ent in entities:
        ent_text = ent['text']
        ent_label = ent['label']
        line_number = ent['line_no']

        if previous_line_number and line_number - previous_line_number > 10:
            contact = {ent_label: [ent_text]}

        if ent_label in ['TITLE', 'PERSON']:
            ent_text = title_except(ent_text)

        if ent['label'] in ['LAW_CAT']:
            continue

        if ent_label in contact:
            if ent_text not in contact[ent_label]:
                contact[ent_label].append(ent_text)
        else:
            contact[ent_label] = [ent_text]

        previous_line_number = ent['line_no']

    return contact


def pp_contact_name(contact, leave_case=False):
    split_name_parts = pp.parse(contact['PERSON'])
    for split_name_part in split_name_parts:
        if split_name_part[1] in ['GivenName', 'Surname', 'MiddleName']:
            contact[split_name_part[1]] = split_name_part[0].lower() if not leave_case else split_name_part[0]
    return contact


def get_possible_email(contact_name, email):
    split_name_parts = pp.parse(contact_name)
    given_name = ''
    surname = ''
    for split_name_part in split_name_parts:
        if split_name_part[1] == 'Surname':
            surname = split_name_part[0].lower()
        if split_name_part[1] == 'GivenName':
            given_name = split_name_part[0].lower()
    email = email.lower()
    email_parts = email_split(email)
    possible_emails = {}
    domain = email_parts.domain
    surname_first_letter = surname[0] if len(surname) else ''
    given_name_first_letter = given_name[0] if len(given_name) else ''

    possible_emails['surname'] = "%s@%s" % (surname, domain)
    possible_emails['given_name'] = "%s@%s" % (given_name, domain)
    possible_emails['given_name|surname'] = "%s%s@%s" % (given_name, surname, domain)
    possible_emails['given_name|.|surname'] = "%s.%s@%s" % (given_name, surname, domain)
    possible_emails['given_name|-|surname'] = "%s-%s@%s" % (given_name, surname, domain)
    possible_emails['given_name|_|surname'] = "%s_%s@%s" % (given_name, surname, domain)
    possible_emails['surname|given_name'] = "%s%s@%s" % (given_name, surname, domain)
    possible_emails['surname|.|given_name'] = "%s.%s@%s" % (surname, given_name, domain)
    possible_emails['surname|-|given_name'] = "%s-%s@%s" % (surname, given_name, domain)
    possible_emails['surname|_|given_name'] = "%s_%s@%s" % (surname, given_name, domain)
    possible_emails['surname0|.|given_name'] = "%s.%s@%s" % (surname_first_letter, given_name, domain)
    possible_emails['surname0|given_name'] = "%s%s@%s" % (surname_first_letter, given_name, domain)
    possible_emails['surname0|-|given_name'] = "%s-%s@%s" % (surname_first_letter, given_name, domain)
    possible_emails['surname0|_|given_name'] = "%s_%s@%s" % (surname_first_letter, given_name, domain)
    possible_emails['given_name0|.|surname'] = "%s.%s@%s" % (given_name_first_letter, surname, domain)
    possible_emails['given_name0|surname'] = "%s%s@%s" % (given_name_first_letter, surname, domain)
    possible_emails['given_name0|-|surname'] = "%s-%s@%s" % (given_name_first_letter, surname, domain)
    possible_emails['given_name0|_|surname'] = "%s_%s@%s" % (given_name_first_letter, surname, domain)
    possible_emails['given_name|.|surname0'] = "%s.%s@%s" % (given_name, surname_first_letter, domain)
    possible_emails['given_name|surname0'] = "%s%s@%s" % (given_name, surname_first_letter, domain)
    possible_emails['given_name|-|surname0'] = "%s-%s@%s" % (given_name, surname_first_letter, domain)
    possible_emails['given_name|_|surname0'] = "%s_%s@%s" % (given_name, surname_first_letter, domain)
    possible_emails['surname|.|given_name0'] = "%s.%s@%s" % (surname, given_name_first_letter, domain)
    possible_emails['|surname|given_name0'] = "%s%s@%s" % (surname, given_name_first_letter, domain)
    possible_emails['surname|-|given_name0'] = "%s-%s@%s" % (surname, given_name_first_letter, domain)
    possible_emails['surname|_|given_name0'] = "%s_%s@%s" % (surname, given_name_first_letter, domain)

    for possible_pattern, possible_email in possible_emails.items():
        if possible_email == email:
            pattern = possible_pattern
            return {'pattern': pattern, 'email': possible_email}

    return None
