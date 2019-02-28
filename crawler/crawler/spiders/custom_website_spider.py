import spacy
from django.conf import settings
import scrapy
from spacy.tokens.span import Span

from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2
from soleadify_ml.utils.SpiderUtils import is_phone_getter


class CustomWebsiteSpider(scrapy.Spider):
    name = 'CustomWebsiteSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [WebsitePagePipelineV2]
    contacts = {}
    emails = []

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        Span.set_extension('is_phone', getter=is_phone_getter, force=True)
        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'response': response})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
