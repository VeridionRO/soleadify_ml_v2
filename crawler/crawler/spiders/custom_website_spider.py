import socket
from soleadify_ml.utils.SocketUtils import connect
import scrapy
from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2


class CustomWebsiteSpider(scrapy.Spider):
    name = 'CustomWebsiteSpider'
    allowed_domains = ['*']
    start_urls = []
    pipeline = [WebsitePagePipelineV2]
    contacts = {}
    emails = []
    cached_docs = {}

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', 50010)

        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'response': response})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
