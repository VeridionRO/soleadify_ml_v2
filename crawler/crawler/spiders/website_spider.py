import logging
import socket
from soleadify_ml.utils.SocketUtils import connect
import scrapy
from scrapy.http import Request, HtmlResponse
from scrapy.linkextractors import LinkExtractor

from crawler.items import WebsitePageItem
from crawler.pipelines.website_page_pipeline_v2 import WebsitePagePipelineV2
from soleadify_ml.models.website import Website
from soleadify_ml.models.website_contact_meta import WebsiteContactMeta
from soleadify_ml.models.website_contact import WebsiteContact

logger = logging.getLogger('soleadify_ml')


class WebsiteSpider(scrapy.Spider):
    name = 'WebsiteSpider'
    allowed_domains = ['*']
    start_urls = []
    pages = []
    pipeline = [WebsitePagePipelineV2]
    contacts = {}
    website = None
    soc_spacy = None
    emails = []
    links = []
    cached_docs = {}

    def __init__(self, website_id, **kw):
        self.website = Website.objects.get(pk=website_id)
        super(WebsiteSpider, self).__init__(**kw)

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', 50010)

        if self.website:
            self.url = self.website.link
            self.allowed_domains = [self.website.domain]
            self.link_extractor = LinkExtractor()

    def start_requests(self):
        logger.debug('start website: ' + self.url)
        return [Request(self.url, callback=self.parse, dont_filter=True)]

    def parse(self, response):
        page = self._get_item(response)
        r = [page]
        r.extend(self._extract_requests(response))

        return r

    def _get_item(self, response):
        try:
            item = WebsitePageItem({'response': response})
            return item
        except AttributeError as exc:
            logger.error(str(exc))
            pass

    def _extract_requests(self, response):
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            r.extend(Request(x.url, callback=self.parse) for x in links)
        return r

    def close(self, spider):
        metas = {}
        for key, contact in self.contacts.items():
            for email in self.emails:
                WebsiteContact.attach_email(contact, email)

            url = contact['URL']
            website_contact = self.website.extract_contact(contact)
            if not website_contact.id:
                website_contact.save()
            for _type, items in contact.items():
                for item in items:
                    key = str(website_contact.id) + str(_type) + str(item)
                    website_contact_meta = WebsiteContactMeta(website_contact_id=website_contact.id, meta_key=_type,
                                                              meta_value=item, page=url)
                    website_contact_meta.update_phone_value(self.website.get_country_code())
                    metas[key] = website_contact_meta
            WebsiteContactMeta.objects.bulk_create(metas.values(), ignore_conflicts=True)
        logger.debug('end website: ' + self.url)
