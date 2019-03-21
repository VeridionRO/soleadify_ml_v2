import json
import socket
import scrapy
import spacy
from django.conf import settings
from spacy.tokens.doc import Doc
from spacy.tokens.span import Span

from soleadify_ml.utils.SocketUtils import connect
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
    spacy_model = None
    tags = []
    line_numbers = []

    def __init__(self, links, **kwargs):
        self.start_urls.append(links)
        # self.start_urls = []
        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        Span.set_extension('line_number', getter=TagLinkSpider.line_number_getter, force=True)
        Doc.set_extension('lines', getter=TagLinkSpider.get_lines, setter=TagLinkSpider.set_lines)
        Doc.set_extension('_lines', default=list())

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', settings.SPACY_PORT)

        super().__init__(**kwargs)

    def parse(self, response):
        yield WebsitePageItem({'text': get_text_from_element(html=response.text), 'link': response.url})

    def close(self, spider):
        with open('/Users/mihaivinaga/Work/soleadify_ml_v2/soleadify_ml/files/1.json', 'w') as the_file:
            for tag in self.tags:
                the_file.write(json.dumps(tag) + "\n")

    @staticmethod
    def line_number_getter(token):
        start_char = token.start_char
        line_numbers = token.doc._.lines
        for key, line_no in enumerate(line_numbers):
            if start_char < line_no:
                return key
        return 0

    @staticmethod
    def get_lines(doc):
        # get lines from internal attribute
        return doc._._lines

    @staticmethod
    def set_lines(doc, value):
        # append value to existing list
        doc._._lines = value
