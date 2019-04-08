from django_mysql.models import EnumField
from django.db import models
from soleadify_ml.models.website_page import WebsitePage
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.models.website_location import WebsiteLocation
from soleadify_ml.utils.SpiderUtils import pp_contact_name


class Website(models.Model):
    id = models.IntegerField(primary_key=True)
    scheme = models.CharField(max_length=10)
    domain = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    redirect_domain = models.CharField(max_length=255)
    redirect_link = models.CharField(max_length=255)
    site_value = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    contact_state = EnumField(choices=['pending', 'working', 'finished'])
    country_codes = []

    class Meta:
        db_table = 'websites'

    def get_pages(self):
        """
        get pages of a website
        :return: the list of page objects
        """
        pages = WebsitePage.objects.filter(website_id=self.id).all()
        return pages

    def extract_contact(self, dirty_contact, score):
        pp_contact_name(dirty_contact)
        first_name = dirty_contact['GivenName'] if 'GivenName' in dirty_contact else None
        last_name = dirty_contact['Surname'] if 'Surname' in dirty_contact else None
        website_contact = WebsiteContact.objects.filter(website_id=self.id, first_name=first_name,
                                                        last_name=last_name).first()
        if not website_contact:
            website_contact = WebsiteContact(
                website_id=self.id, name=dirty_contact['PERSON'],
                first_name=dirty_contact['GivenName'] if 'GivenName' in dirty_contact else None,
                last_name=dirty_contact['Surname'] if 'Surname' in dirty_contact else None,
                middle_name=dirty_contact['MiddleName'] if 'MiddleName' in dirty_contact else None,
                score=score)
        else:
            website_contact.score = website_contact.score | score

        dirty_contact.pop('PERSON', None)
        dirty_contact.pop('GivenName', None)
        dirty_contact.pop('Surname', None)
        dirty_contact.pop('MiddleName', None)
        dirty_contact.pop('URL', None)
        dirty_contact.pop('DONE', None)

        return website_contact

    def get_country_codes(self, refresh=False):
        if len(self.country_codes) == 0 or refresh:
            country_code_set = WebsiteLocation.objects. \
                                   values('country_code', 'occurrences', 'postcode', 'road', 'house_number'). \
                                   filter(website_id=self.id). \
                                   order_by('-occurrences', '-postcode', '-road', '-house_number')[:3]
            for country_code in country_code_set:
                self.country_codes.append(country_code['country_code'].upper())

        return self.country_codes

    def get_link(self):
        return self.redirect_link if self.redirect_link else self.link
