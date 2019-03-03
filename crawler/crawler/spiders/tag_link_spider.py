import socket
from soleadify_ml.utils.SocketUtils import connect
import scrapy
# from crawler.pipelines.tag_link_pipeline import TagLinkPipeline
from crawler.items import WebsitePageItem
from soleadify_ml.utils.SpiderUtils import get_text_from_element


class TagLinkSpider(scrapy.Spider):
    name = 'TagLinkSpider'
    allowed_domains = ['*']
    start_urls = []
    # pipeline = [TagLinkPipeline]
    contacts = {}
    emails = []
    spacy_model = None

    def __init__(self, link, **kwargs):
        self.start_urls.append(link)

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', 50010)

        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'text': get_text_from_element(response.text), 'link': response.url})

    def close(self, spider):
        for key, contact in self.contacts.items():
            print(contact)
