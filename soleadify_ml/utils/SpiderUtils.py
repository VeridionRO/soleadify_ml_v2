import json
import logging
import functools
import re
import probablepeople as pp
from email_split import email_split

logger = logging.getLogger('soleadify_ml')
contacts = {}


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


def title_except(s):
    exceptions = ['a', 'an', 'of', 'the', 'is']
    word_list = re.split(' ', s)  # re.split behaves as expected
    final = [word_list[0].capitalize()]
    for word in word_list[1:]:
        final.append(word if word in exceptions else word.capitalize())
    return " ".join(final)


def pp_contact_name(contact, leave_case=False):
    split_name_parts = pp.parse(contact['PERSON'])
    for split_name_part in split_name_parts:
        if split_name_part[1] in ['GivenName', 'Surname', 'MiddleName']:
            name = re.sub(r"[^a-zA-Z-']+", '', split_name_part[0])
            contact[split_name_part[1]] = name.lower() if not leave_case else name
    return contact


def get_possible_email(contact_name, email):
    split_name_parts = []
    try:
        split_name_parts = pp.parse(contact_name)
    except TypeError as e:
        logger.error("possible_email: " + str(e) + ' - ' + json.dumps(contact_name))
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
    possible_emails['surname0|given_name0'] = "%s%s@%s" % (surname_first_letter, given_name_first_letter, domain)
    possible_emails['given_name0|surname0'] = "%s%s@%s" % (given_name_first_letter, surname_first_letter, domain)
    possible_emails['surname'] = "%s@%s" % (surname, domain)
    possible_emails['given_name'] = "%s@%s" % (given_name, domain)

    for possible_pattern, possible_email in possible_emails.items():
        if possible_email == email:
            pattern = possible_pattern
            return {'pattern': pattern, 'email': possible_email}

    return None


def merge_dicts(dic1, dic2):
    for key, values2 in dic2.items():
        if key in ['ORG', 'TITLE', 'EMAIL', 'PHONE', 'PERSON']:
            if key in dic1:
                values1 = dic1[key]
                if not isinstance(values1, list) and not isinstance(values2, list):
                    if values1 != values2:
                        dic1[key] = [values1, values2]

                elif not isinstance(values1, list) and isinstance(values2, list):
                    dic1[key] = list(set(values2).union(set([values1])))
                elif isinstance(values1, list) and not isinstance(values2, list):
                    dic1[key] = list(set(values1).union(set([values2])))
                else:
                    dic1[key] = list(set(values1).union(set(values2)))

            else:
                dic1[key] = values2
