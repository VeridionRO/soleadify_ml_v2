import hashlib
import re

import phonenumbers
from django.db import models
from soleadify_ml.models.website_contact_meta import WebsiteContactMeta
from soleadify_ml.utils.SpiderUtils import pp_contact_name, merge_dicts


class WebsiteContact(models.Model):
    models.AutoField(primary_key=True)
    website_id = models.IntegerField()
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'website_contacts'

    @staticmethod
    def add_contact(contact, contacts, spider, from_tuple=True):
        new_contact = {}
        if from_tuple:
            for key, contact_part in contact.items():
                if key == 'URL':
                    continue
                new_contact[key] = [value[0] for value in contact_part]
        else:
            new_contact = contact

        name = new_contact['PERSON'][0]
        new_contact['URL'] = contact['URL']
        new_contact['PERSON'] = name.title()
        name_key = WebsiteContact.get_name_key(name)

        if 'EMAIL' in new_contact:
            emails = new_contact['EMAIL']

            for email in emails:
                if email in spider.emails:
                    spider.emails.remove(email)

        if 'TITLE' in new_contact:
            titles = new_contact['TITLE']
            new_titles = []
            for job_title in titles:
                new_titles.append(job_title)
                pass
            new_contact['TITLE'] = new_titles

        if name_key in contacts:
            merge_dicts(contacts[name_key], new_contact)
        else:
            contacts[name_key] = new_contact

        important_keys = ['PERSON', 'EMAIL', 'PHONE']
        contact_keys = new_contact.keys()
        important_keys_intersection = list(set(important_keys) & set(contact_keys))

        if len(important_keys_intersection) >= 3:
            contacts[name_key]['DONE'] = True
        else:
            contacts[name_key]['DONE'] = False

        return contacts[name_key]

    @staticmethod
    def get_name_key(name):
        pp_name = pp_contact_name({'PERSON': name})
        name_key = ''

        if 'GivenName' in pp_name:
            name_key += pp_name['GivenName']

        if 'Surname' in pp_name:
            name_key += pp_name['Surname']

        name_key = re.sub(r'[^a-zA-Z]+', '', name_key)
        return hashlib.md5(name_key.encode()).hexdigest()

    @staticmethod
    def save_contact(website, contact, score=10):
        metas = {}
        url = contact['URL']
        website_contact = website.extract_contact(contact)
        if not website_contact.id:
            website_contact.save()
        for _type, items in contact.items():
            for item in items:
                key = str(website_contact.id) + str(_type) + str(item)
                website_contact_meta = WebsiteContactMeta(website_contact_id=website_contact.id, meta_key=_type,
                                                          meta_value=item, page=url, score=score)
                website_contact_meta.update_phone_value(website.get_country_codes())
                metas[key] = website_contact_meta
        WebsiteContactMeta.objects.bulk_create(metas.values(), ignore_conflicts=True)
