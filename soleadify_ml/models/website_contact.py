from django.db import models
import probablepeople as pp
import re
from email_split import email_split


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

    @staticmethod
    def add_contact(contact, saved_contacts, stored_emails=(), from_tuple=True):
        new_contact = {}
        if from_tuple:
            for key, contact_part in contact.items():
                new_contact[key] = [value[0] for value in contact_part]
        else:
            new_contact = contact

        name = new_contact['PERSON'][0]
        new_contact['PERSON'] = name
        split_name_parts = pp.parse(name)
        name_key = re.sub(r'[^a-zA-Z]+', '', name).lower()

        if 'EMAIL' in new_contact:
            emails = new_contact['EMAIL']

            for email in emails:
                if email in stored_emails:
                    stored_emails.remove(email)

        for split_name_part in split_name_parts:
            if split_name_part[1] in ['GivenName', 'Surname', 'MiddleName']:
                new_contact[split_name_part[1]] = split_name_part[0].lower()

        if name_key in saved_contacts:
            WebsiteContact.merge_dicts(saved_contacts[name_key], new_contact)
        else:
            saved_contacts[name_key] = new_contact

        return saved_contacts[name_key]

    @staticmethod
    def attach_email(contact, email):
        email = email.lower()
        email_parts = email_split(email)
        possible_emails = {}
        pattern = None
        domain = email_parts.domain
        surname = contact['Surname'].lower() if 'Surname' in contact else ''
        given_name = contact['GivenName'].lower() if 'GivenName' in contact else ''
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
                contact['EMAIL'] = [possible_email]

                break

        return pattern

    @staticmethod
    def merge_dicts(dic1, dic2):
        for key, values in dic2.items():
            if key in ['ORG', 'TITLE', 'EMAIL', 'PHONE']:
                if key in dic1:
                    dic1[key] = list(set(dic1[key]).union(set(values)))
                    pass
                else:
                    dic1[key] = values
