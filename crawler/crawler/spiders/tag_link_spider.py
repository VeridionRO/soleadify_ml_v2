import json
import socket
import scrapy
from django.conf import settings

from crawler.spiders.spider_common import SpiderCommon
from soleadify_ml.utils.SocketUtils import connect
from crawler.pipelines.tag_link_pipeline import TagLinkPipeline
from crawler.items import WebsitePageItem


class TagLinkSpider(scrapy.Spider, SpiderCommon):
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

        import spacy
        from spacy.tokens.doc import Doc
        from spacy.tokens.span import Span

        self.spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        Span.set_extension('line_number', getter=TagLinkSpider.line_number_getter, force=True)
        Doc.set_extension('lines', getter=TagLinkSpider.get_lines, setter=TagLinkSpider.set_lines)
        Doc.set_extension('_lines', default=list())

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', settings.SPACY_PORT)

        super().__init__(**kwargs)

    def parse(self, response):
        for file in ["Associate at A Center For Children & Family Law", "Attorney at David A. Mahl, Esq.",
                     "Chair, Restaurant Sector Team at Akerman LLP", "Counsel at Day Pitney LLP",
                     "Counsel at Grey & Grey, LLP", "Managing Partner at Townsend & Lockett",
                     "Member at Aber, Goldlust, Baker & Over", "Partner at Law Offices of Johnson, Crump, Walters,",
                     "Principal at The Law Firm of L. Palmer Foret, P.C.", "Staff Attorney at The Crone Law Firm, PLC"]:
            with open('/Users/mihaivinaga/Work/soleadify_ml_v2/soleadify_ml/files/' + file) as the_file:
                yield WebsitePageItem({'text': the_file.read(), 'link': ''})

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
