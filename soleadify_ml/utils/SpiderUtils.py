import json
import logging
import functools
import re
import probablepeople as pp
import tldextract
from email_split import email_split

from soleadify_ml import settings

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
    split_name_parts = pp.parse(contact['PERSON'], type='person')
    for split_name_part in split_name_parts:
        if split_name_part[1] in ['GivenName', 'Surname', 'MiddleName']:
            name = re.sub(r"[^a-zA-Z-']+", '', split_name_part[0])
            contact[split_name_part[1]] = name.lower() if not leave_case else name
    return contact


def get_possible_email(contact_name, email):
    split_name_parts = []
    try:
        split_name_parts = pp.parse(contact_name, type='person')
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

    domain_split = email.split('@')
    if len(domain_split):
        email_domain = domain_split[0]
        if surname and given_name and surname in email_domain and given_name in email_domain:
            return {'pattern': '_surname_given_name_', 'email': email}

    return None


valid_emails = {}


def check_email(email):
    global valid_emails

    if email in valid_emails:
        return valid_emails[email]

    p = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z-.]{2,}')
    ignored_suffixes = ['gif', 'jpg', 'png', 'swf', 'psd', 'bmp', 'tiff', 'tiff', 'jpc', 'jp2',
                        'jpf', 'jb2', 'swc', 'aiff', 'wbmp', 'xbm', 'pdf', 'jpeg', 'docx', 'json', 'doc']
    if not re.search(p, email):
        logger.debug("ignored email regex %s", email)
        valid_emails[email] = False
        return None

    tld_domain = tldextract.extract(email)
    if hasattr(tld_domain, 'suffix'):
        suffix = tld_domain.suffix
        if suffix in ignored_suffixes:
            logger.debug("ignored email suffix %s", email)
            valid_emails[email] = False
            return None

    if hasattr(tld_domain, 'domain'):
        domain = tld_domain.domain
        if domain in ignored_suffixes:
            logger.debug("ignored email domain %s", email)
            valid_emails[email] = False
            return None

    with open(settings.STOP_EMAILS_FILE) as f:
        stop_emails_file = json.load(f)
        if email in stop_emails_file:
            logger.debug("ignored email stop_emails %s", email)
            valid_emails[email] = False
            return None

    valid_emails[email] = True
    return email


def merge_dicts(dic1, dic2):
    for key, values2 in dic2.items():
        if key in ['ORG', 'TITLE', 'EMAIL', 'PHONE', 'PERSON', 'LAW_CAT']:
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
