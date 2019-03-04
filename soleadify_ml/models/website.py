from django_mysql.models import EnumField
from django.db import models
from django.db.models import Count
from soleadify_ml.models.website_page import WebsitePage
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.models.website_location import WebsiteLocation


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
    country_code = None

    class Meta:
        db_table = 'websites'

    def get_pages(self):
        """
        get pages of a website
        :return: the list of page objects
        """
        pages = WebsitePage.objects.filter(website_id=self.id).all()
        return pages

    def extract_contact(self, dirty_contact):
        website_contact = WebsiteContact.objects.filter(website_id=self.id, name=dirty_contact['PERSON']).first()
        if not website_contact:
            website_contact = WebsiteContact(
                website_id=self.id, name=dirty_contact['PERSON'],
                first_name=dirty_contact['GivenName'] if 'GivenName' in dirty_contact else None,
                last_name=dirty_contact['Surname'] if 'Surname' in dirty_contact else None,
                middle_name=dirty_contact['MiddleName'] if 'MiddleName' in dirty_contact else None)
        dirty_contact.pop('PERSON', None)
        dirty_contact.pop('GivenName', None)
        dirty_contact.pop('Surname', None)
        dirty_contact.pop('MiddleName', None)
        dirty_contact.pop('URL', None)
        dirty_contact.pop('DONE', None)

        return website_contact

    def get_country_code(self, refresh=False):
        if not self.country_code or refresh:
            country_code_set = WebsiteLocation.objects. \
                annotate(count_website_id=Count('website_id')). \
                values('country_code', 'count_website_id'). \
                filter(website_id=self.id).order_by('-count_website_id').first()
            if country_code_set:
                self.country_code = country_code_set['country_code'].upper()

        return self.country_code
