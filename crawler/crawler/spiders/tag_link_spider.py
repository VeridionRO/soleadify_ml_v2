import scrapy
import spacy
from django.conf import settings
from spacy.tokens import Span

from crawler.pipelines.tag_link_pipeline import TagLinkPipeline
from crawler.items import WebsitePageItem
from soleadify_ml.utils.SpiderUtils import get_text_from_element, is_phone_getter


class TagLinkSpider(scrapy.Spider):
    name = 'TagLinkSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [TagLinkPipeline]
    contacts = {}
    emails = []
    spacy_model = None

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        Span.set_extension('is_phone', getter=is_phone_getter, force=True)
        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'text': get_text_from_element(response.text), 'link': response.url})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
