import logging
import socket
from soleadify_ml.utils.SocketUtils import connect
import scrapy
from scrapy.http import Request, HtmlResponse
from scrapy.linkextractors import LinkExtractor
from django.conf import settings
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
    url = None
    emails = []
    links = []
    cached_docs = {}
    ignored_links = ['tel:', 'mailto:']

    def __init__(self, website_id, **kw):
        self.website = Website.objects.get(pk=website_id)
        super(WebsiteSpider, self).__init__(**kw)

        self.soc_spacy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc_spacy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connect(self.soc_spacy, '', settings.SPACY_PORT)

        if self.website and self.website.contact_state == 'pending':
            self.url = self.website.link
            self.allowed_domains = [self.website.domain]
            self.link_extractor = LinkExtractor()

            self.website.contact_state = 'working'
            self.website.save(update_fields=['contact_state'])
        elif self.website and self.website.contact_state != 'pending':
            logger.debug('already processed: ' + self.website.link)
        else:
            logger.debug("couldn't find website: ")

    def start_requests(self):
        if self.url:
            logger.debug('start website: ' + self.url)
            return [Request(self.url, callback=self.parse, dont_filter=True)]
        else:
            return []

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
        parsed_links = []
        if isinstance(response, HtmlResponse):
            def sort_links(current_link):
                url = current_link.url.lower()
                url_text = current_link.text
                priority_pages = {'team': 8, 'meet': 7, 'member': 6, 'detail': 5, 'directory': 4, 'contact': 3,
                                  'about': 2, 'find': 1}
                for key, value in priority_pages.items():
                    if key in url or key in url_text:
                        return value
                return 0

            links = self.link_extractor.extract_links(response)
            links = sorted(links, key=sort_links, reverse=True)
            for link in links:
                parsed_links.append(link) if not self.is_ignored(link) else None

            r.extend(Request(x.url, callback=self.parse) for x in parsed_links)
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

        if self.url:
            self.website.contact_state = 'finished'
            self.website.save(update_fields=['contact_state'])

            logger.debug('end website: ' + self.website.link)

    def is_ignored(self, link):
        for ignored in self.ignored_links:
            if ignored in link.url:
                return True
        return False
