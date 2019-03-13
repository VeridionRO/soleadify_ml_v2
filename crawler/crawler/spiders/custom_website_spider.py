import socket

from django.conf import settings

from soleadify_ml.utils.SocketUtils import connect
import scrapy
from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2
from soleadify_ml.utils.SpiderUtils import get_possible_email


class CustomWebsiteSpider(scrapy.Spider):
    name = 'CustomWebsiteSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [WebsitePagePipelineV2]
    contacts = {}
    secondary_contacts = {}
    emails = []
    website_metas = {'LAW_CAT': [], 'ORG': []}
    cached_docs = {}

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', settings.SPACY_PORT)

        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'response': response})

    def close(self, spider):
        for key, contact in self.contacts.items():
            for email in self.emails:
                if 'EMAIL' in contact:
                    break
                possible_email = get_possible_email(contact['PERSON'], email)
                if possible_email:
                    contact['EMAIL'] = [possible_email['email']]
            print(contact)
        print('---secondary---')
        for key, contact in self.secondary_contacts.items():
            if key not in self.contacts:
                print(contact)
        print('---metas---')
        print(self.website_metas)
