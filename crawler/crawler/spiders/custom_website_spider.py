import socket
import scrapy
import iso3166
import tldextract
from django.conf import settings
from scrapy.utils.response import open_in_browser
from crawler.spiders.spider_common import SpiderCommon
from soleadify_ml.models.website_contact import WebsiteContact
from soleadify_ml.utils.SocketUtils import connect
from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2
from soleadify_ml.utils.SpiderUtils import get_possible_email


class CustomWebsiteSpider(scrapy.Spider, SpiderCommon):
    name = 'CustomWebsiteSpider'
    start_urls = []
    pipeline = [WebsitePagePipelineV2]
    secondary_contacts = {}
    cached_docs = {}
    country_codes = []

    def __init__(self, link, **kw):
        self.start_urls.append(link)
        try:
            country_code = tldextract.extract(link).suffix.upper()
            country = iso3166.countries_by_alpha2[country_code]
        except KeyError:
            country = iso3166.countries_by_alpha2['US']

        self.country_codes.append(country.alpha2)
        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', settings.SPACY_PORT)

        super(CustomWebsiteSpider, self).__init__(**kw)

    def parse(self, response):
        yield WebsitePageItem({'response': response})

    def close(self, spider):
        for key, contact in self.contacts.items():
            for email in self.website_metas['EMAIL']:
                if 'EMAIL' in contact:
                    break
                possible_email = get_possible_email(contact['PERSON'], email)
                if possible_email:
                    contact['EMAIL'] = [possible_email['email']]
            if WebsiteContact.valid_contact(contact, 2):
                contact.pop('URL', None)
                print(contact)

        print('---metas---')
        print(self.website_metas)
