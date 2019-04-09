import hashlib
import re

from bitfield import BitField
from django.db import models
from soleadify_ml.models.website_contact_meta import WebsiteContactMeta
from soleadify_ml.utils.SpiderUtils import pp_contact_name, merge_dicts


class WebsiteContact(models.Model):
    id = models.AutoField(primary_key=True)
    website_id = models.IntegerField()
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    score = BitField(flags=(
        ('has_org', 'has organization', 1),
        ('has_title', 'has title', 2),
        ('has_phone', 'has phone', 4),
        ('has_email', 'has email', 8),
        ('has_unique_phone', 'has unique phone', 16),
        ('has_unique_email', 'has unique email', 32),
        ('has_matching_email', 'has matching email', 64),
    ))

    class Meta:
        db_table = 'website_contacts'

    @staticmethod
    def add_contact(contact, spider, from_tuple=True):
        contacts = spider.contacts
        new_contact = {}
        if from_tuple:
            for key, contact_part in contact.items():
                if key == 'URL':
                    continue
                new_contact[key] = [value[0] for value in contact_part]
        else:
            new_contact = contact

        name = new_contact['PERSON'][0]
        name_parts = WebsiteContact.get_name_key(name)
        name_key = name_parts['name_key']
        new_name = name_parts['name']

        new_contact['URL'] = contact['URL']
        new_contact['PERSON'] = new_name.title()

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
        new_name = ''

        if 'GivenName' in pp_name:
            new_name += pp_name['GivenName']

        if 'Surname' in pp_name:
            new_name += ' ' + pp_name['Surname']

        if not ('GivenName' in pp_name and 'Surname' in pp_name):
            new_name = name

        name_key = re.sub(r'[^a-zA-Z]+', '', new_name)
        return {'name_key': hashlib.md5(name_key.encode('utf8')).hexdigest(),
                'name': new_name}

    @staticmethod
    def save_contact(website, contact, score):
        metas = {}
        url = contact['URL']
        website_contact = website.extract_contact(contact, score)
        website_contact.save()
        for _type, items in contact.items():
            for item in items:
                key = str(website_contact.id) + str(_type) + str(item)
                website_contact_meta = WebsiteContactMeta(website_contact_id=website_contact.id, meta_key=_type,
                                                          meta_value=item, page=url)
                website_contact_meta.update_phone_value(website.get_country_codes())
                metas[key] = website_contact_meta
        WebsiteContactMeta.objects.bulk_create(metas.values(), ignore_conflicts=True)
        return website_contact

    @staticmethod
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
