import json
import logging

from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SpiderUtils import pp_contact_name

logger = logging.getLogger('soleadify_ml')


class SpiderCommon:
    contacts = {}

    def contact_done(self, name, url):
        name_parts = WebsiteContact.get_name_key(name)
        name_key = name_parts['name_key']

        if name_key in self.contacts and self.contacts[name_key]['DONE']:
            logger.debug("contact cached: %s:%s:", json.dumps(self.contacts[name_key]), url)
            return True
        return False

    def get_person_dom_elements(self, response, person_name):
        person_elements = response.xpath('//*[contains(text(),"%s")]' % person_name)
        if len(person_elements) == 0:
            person_elements = response.xpath('//*[contains(.,"%s")]' % person_name)
            if len(person_elements) > 0:
                person_elements = [person_elements[-1]]
            else:
                pp_name = pp_contact_name({'PERSON': person_name}, True)
                if 'Surname' in pp_name:
                    pass
                    if 'GivenName' in pp_name:
                        xpath = '//*[contains(.,"%s") and contains(.,"%s")]' % \
                                (pp_name['Surname'], pp_name['GivenName'])
                        person_elements = response.xpath(xpath)
                        if len(person_elements) > 0:
                            person_elements = [person_elements[-1]]

        return person_elements
