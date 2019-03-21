import json
import logging
from collections import Counter

from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import pp_contact_name, get_possible_email

logger = logging.getLogger('soleadify_ml')


class SpiderCommon:
    contacts = {}
    temp_contacts = {}
    max_pages = 500
    website_metas = {
        'EMAIL': Counter(),
        'PHONE': Counter(),
        'ORG': Counter(),
        'LAW_CAT': Counter(),
    }

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
                        if len(person_elements) > 0:
                            person_elements = [person_elements[-1]]

        return person_elements

    def get_person_names(self, docs):
        person_names = []
        consecutive_persons = 0
        previous_person = None
        website_metas_temp = {}
        for ent in docs:
            label = ent['label']
            text = ent['text']
            if label in ['EMAIL', 'PHONE', 'ORG', 'LAW_CAT']:
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
        crawled_pages = 500 - self.max_pages
        metas = self.website_metas[key]
        if value in metas and metas[value] / crawled_pages < 0.5:
            del self.website_metas[key][value]
