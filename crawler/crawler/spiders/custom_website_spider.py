import scrapy
from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2
from soleadify_ml.utils.SpiderUtils import get_text_from_element


class CustomWebsiteSpider(scrapy.Spider):
    name = 'CustomWebsiteSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [WebsitePagePipelineV2]
    contacts = {}
    emails = []

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)
        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'response': response})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
