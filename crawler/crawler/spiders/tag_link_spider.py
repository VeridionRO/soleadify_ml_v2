import scrapy
from crawler.pipelines.tag_link_pipeline import TagLinkPipeline
from crawler.items import WebsitePageItem
from soleadify_ml.utils.SpiderUtils import get_text_from_element


class TagLinkSpider(scrapy.Spider):
    name = 'TagLinkSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [TagLinkPipeline]
    contacts = {}
    emails = []

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)
        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'text': get_text_from_element(response.text), 'link': response.url})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
