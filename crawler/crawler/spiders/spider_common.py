import time
import hashlib
import json
import logging
import re
from collections import Counter
from lxml import etree
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.models.website_contact_meta import WebsiteContactMeta
from soleadify_ml.utils.HTML2TextV2 import HTML2TextV2
from soleadify_ml.utils.SocketUtils import recv_end
from soleadify_ml.utils.SpiderUtils import pp_contact_name, get_possible_email, merge_dicts, title_except

logger = logging.getLogger('soleadify_ml')


class SpiderCommon:
    texts = {}
    contacts = {}
    temp_contacts = {}
    max_pages = 200
    cached_docs = {}
    soc_spacy = None
    country_codes = []
    added_time = 0
    added_time_v2 = 0
    entities = {}
    cached_contacts = {}
    website_metas = {
        'EMAIL': Counter(),
        'PHONE': Counter(),
        'ORG': Counter(),
    }
    has_contacts = False

    def contact_done(self, name, url):
        name_parts = WebsiteContact.get_name_key(name)
        name_key = name_parts['name_key']

        if name_key in self.contacts and self.contacts[name_key]['DONE']:
            logger.debug("contact cached: %s:%s:", json.dumps(self.contacts[name_key]), url)
            return True
        return False

    def get_person_dom_elements(self, response, person_name):
        person_elements = response.xpath('//body//*[contains(text(),"%s")]' % person_name)
        if len(person_elements) == 0:
            person_elements = response.xpath('//body//*[contains(.,"%s")]' % person_name)
            if len(person_elements) > 0:
                person_elements = [person_elements[-1]]
            else:
                pp_name = pp_contact_name({'PERSON': person_name}, True)
                if 'Surname' in pp_name:
                    pass
                    if 'GivenName' in pp_name:
                        xpath = '//body//*[contains(.,"%s") and contains(.,"%s") and count(ancestor::*) >= 10]' % \
                                (pp_name['Surname'], pp_name['GivenName'])
                        person_elements = response.xpath(xpath)

        return person_elements

    def get_person_names(self, docs):
        person_names = []
        consecutive_persons = 0
        previous_person = None
        website_metas_temp = {}
        for ent in docs:
            label = ent['label']
            text = ent['text']
            if label in ['EMAIL', 'PHONE', 'ORG']:
                if label not in website_metas_temp:
                    website_metas_temp[label] = {}
                website_metas_temp[label][text] = True
            if label == 'PERSON':
                if text != previous_person:
                    consecutive_persons += 1

                    if consecutive_persons < 3 and previous_person:
                        person_names.append(previous_person)

                    previous_person = text
            else:
                consecutive_persons = 0

        if previous_person:
            person_names.append(previous_person)

        for key, metas in website_metas_temp.items():
            self.website_metas[key].update(metas.keys())

        return set(person_names)

    def get_contact_score(self, contact):
        contacts = self.contacts
        score = 0

        if 'ORG' in contact:
            score = score | WebsiteContact.score.has_org
        if 'TITLE' in contact:
            score = score | WebsiteContact.score.has_title
        if 'PHONE' in contact:
            score = score | WebsiteContact.score.has_phone
        if 'EMAIL' in contact:
            score = score | WebsiteContact.score.has_email

        if 'PHONE' in contact:
            phones = contact['PHONE']
            duplicated_phones = []
            for phone in phones:
                for key, temp_contact in contacts.items():
                    if temp_contact == contact:
                        continue
                    if 'PHONE' in temp_contact and phone in temp_contact['PHONE']:
                        duplicated_phones.append(phone)
                        break
            if len(duplicated_phones) != len(phones):
                score = score | WebsiteContact.score.has_unique_phone

            unique_phones = list(set(phones) - set(duplicated_phones))
            for unique_phone in unique_phones:
                self.remove_meta('PHONE', unique_phone)

        if 'EMAIL' in contact:
            emails = contact['EMAIL']
            duplicated_emails = []
            for email in emails:
                for key, temp_contact in contacts.items():
                    if temp_contact == contact:
                        continue
                    if 'EMAIL' in temp_contact and email in temp_contact['EMAIL']:
                        duplicated_emails.append(email)
                        break
            if len(duplicated_emails) != len(emails):
                score = score | WebsiteContact.score.has_unique_email

            unique_emails = list(set(emails) - set(duplicated_emails))
            for unique_email in unique_emails:
                self.remove_meta('EMAIL', unique_email)

        if 'EMAIL' in contact:
            for email in contact['EMAIL']:
                if get_possible_email(contact['PERSON'], email):
                    score = score | WebsiteContact.score.has_matching_email
                    self.remove_meta('EMAIL', email)
                    break

        return score

    def remove_meta(self, key, value):
        crawled_pages = 200 - self.max_pages
        metas = self.website_metas[key]
        if value in metas and metas[value] / crawled_pages < 0.5:
            del self.website_metas[key][value]

    def get_entities(self, text, url):
        new_docs = []
        self.has_contacts = False
        if not text:
            return new_docs
        dom_element_text_key = hashlib.md5(text.encode()).hexdigest()
        try:
            if dom_element_text_key in self.cached_docs:
                new_docs = self.cached_docs[dom_element_text_key]
            else:
                self.soc_spacy.sendall(text.encode('utf8') + '--end--'.encode('utf8'))
                docs = json.loads(recv_end(self.soc_spacy))

                for doc in docs:
                    # if the phone is not valid for the country ignore it
                    if doc['label'] == 'PHONE':
                        valid_phone = WebsiteContactMeta.get_valid_country_phone(self.country_codes, doc['text'])
                        if valid_phone:
                            doc['text'] = valid_phone
                        else:
                            continue
                    new_docs.append(doc)

                self.cached_docs[dom_element_text_key] = new_docs
        except Exception as ve:
            logger.error("%s : %s", url, ve)
            return new_docs

        for doc in new_docs:
            # if the phone is not valid for the country ignore it
            if doc['label'] in ['PHONE', 'EMAIL']:
                self.has_contacts = True

        return new_docs

    def get_text_from_element(self, element=None, html=None):
        if not html:
            html = etree.tostring(element).decode("utf-8")

        text_key = hashlib.md5(html.encode()).hexdigest()

        if text_key in self.texts:
            return self.texts[text_key]
        else:
            converter = HTML2TextV2(bodywidth=0)
            converter.ignore_images = True
            converter.single_line_break = True
            converter.inheader = True
            converter.get_email_phone = True
            converter.emphasis_mark = ' '

            page_text = converter.handle(html)

            replaces = [('(mailto:', ' '), ('mailto:', ' '), ('(tel:', ' '), ('tel:', ' ')]
            for k, v in replaces:
                page_text = page_text.replace(k, v)

            page_text = re.sub(r'[^a-zA-Z0-9@\- ,.:\n&()$_\'|]+', ' ', page_text)
            page_text = re.sub(r'(\s*\n\s*)+', '\n', page_text)
            page_text = re.sub(r'\s\s+', ', ', page_text)
            page_text = re.sub(r'\s\s+', ', ', page_text)
            page_text = re.sub(r',+', ',', page_text)
            page_text = re.sub(r', +', ', ', page_text)

            if 'BEGIN:VCARD' in page_text:
                page_text = page_text.replace(':', '\n')

            self.texts[text_key] = page_text.strip()
            return self.texts[text_key]

    def get_person_from_element(self, person_name, dom_element, previous_contact=None, depth=1, page='',
                                previous_dom_element_text=''):
        dom_element_text = self.get_text_from_element(element=dom_element)
        t1 = time.time()
        required_no = 1
        docs = self.get_entities(dom_element_text, page)
        self.added_time += time.time() - t1
        logger.debug(page + ' - ' + str(self.added_time))

        contact = None
        if self.has_contacts:
            contact = self.enough_for_a_person(docs, person_name, dom_element_text)

        if contact and previous_contact and 'PERSON' in previous_contact and 'PERSON' in contact and len(
                previous_contact['PERSON']) > 0 and len(previous_contact['PERSON']) < len(contact['PERSON']):
            if WebsiteContact.valid_contact(previous_contact, required_no):
                return previous_contact
            else:
                return None

        if contact and WebsiteContact.valid_contact(contact, 4):
            return contact

        if depth > 4 and WebsiteContact.valid_contact(contact, required_no):
            return contact

        if not WebsiteContact.valid_contact(contact, required_no) and \
                WebsiteContact.valid_contact(previous_contact, required_no):
            return previous_contact
        elif depth > 4:
            return None
        else:
            parent = dom_element.getparent()
            if parent is not None:
                new_depth = depth
                if previous_dom_element_text != dom_element_text:
                    new_depth += 1
                previous_dom_element_text = dom_element_text
                return self.get_person_from_element(person_name, parent, contact, new_depth, page,
                                                    previous_dom_element_text)
            elif WebsiteContact.valid_contact(contact, required_no):
                return contact
            elif WebsiteContact.valid_contact(previous_contact, required_no):
                return contact

    def enough_for_a_person(self, docs, contact_name, text):
        contact = self.entities_to_contact(docs, text)

        # this resolves the case when we are on the page of an person and on
        # that page there is mention to another person
        if 'PERSON' in contact and 'EMAIL' in contact and len(contact['EMAIL']) == 1 and len(contact['PERSON']) > 1:
            for current_contact_name in contact['PERSON']:
                possible_email = get_possible_email(current_contact_name, contact['EMAIL'][0])
                if possible_email:
                    current_person_lines = [doc['line_no'] for doc in docs if
                                            current_contact_name.lower() == doc['text'].lower()]
                    has_person = False
                    temp_person_docs = []
                    prev_line = 0
                    new_docs = docs.copy()
                    for doc in docs:
                        if prev_line and prev_line != doc['line_no']:
                            if prev_line not in current_person_lines and has_person:
                                for temp_person_doc in temp_person_docs:
                                    new_docs.remove(temp_person_doc)
                            temp_person_docs = []
                            has_person = False
                        if doc['label'] == 'PERSON':
                            has_person = True
                        prev_line = doc['line_no']
                        temp_person_docs.append(doc)
                    contact = self.entities_to_contact(new_docs, text)
                    contact['PERSON'] = [current_contact_name]
                    if 'EMAIL' in possible_email:
                        contact['EMAIL'] = [possible_email['EMAIL']]
                    break

        if 'PERSON' in contact and len(contact['PERSON']) >= 2:
            new_contact_names = []
            duplicate = False
            for contact_name_2 in contact['PERSON']:
                if contact_name == contact_name_2:
                    continue

                name_keys = ['GivenName', 'Surname']

                if contact_name in self.cached_contacts:
                    pp_name = self.cached_contacts[contact_name]
                else:
                    pp_name = pp_contact_name({'PERSON': contact_name})
                    self.cached_contacts[contact_name] = pp_name

                if contact_name_2 in self.cached_contacts:
                    pp_name_2 = self.cached_contacts[contact_name_2]
                else:
                    pp_name_2 = pp_contact_name({'PERSON': contact_name_2})
                    self.cached_contacts[contact_name_2] = pp_name_2

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

    def entities_to_contact(self, entities, text):
        text_key = hashlib.md5(text.encode()).hexdigest()
        if text_key in self.entities:
            contact = self.entities[text_key]
        else:
            contact = {}
            final_contact = {}
            previous_line_number = None
            for ent in entities:
                ent_text = ent['text']
                ent_label = ent['label']
                line_number = ent['line_no']

                if previous_line_number and line_number - previous_line_number > 10:
                    if len(contact.keys()) > 0 and 'PERSON' in contact:
                        merge_dicts(final_contact, contact)

                    contact = {ent_label: [ent_text]}

                if ent_label in ['TITLE', 'PERSON']:
                    ent_text = title_except(ent_text)

                if ent_label in contact:
                    if ent_text not in contact[ent_label]:
                        contact[ent_label].append(ent_text)
                else:
                    contact[ent_label] = [ent_text]

                previous_line_number = ent['line_no']

            contact = final_contact if len(final_contact.keys()) else contact
            self.entities[text_key] = contact

        return contact.copy()
