import scrapy

from crawler.pipelines.custom_link_pipeline import CustomLinkPipeline
from soleadify_ml.utils.SpiderUtils import get_text_from_element


class CustomLinksSpider(scrapy.Spider):
    name = 'CustomLinksSpider'
    allowed_domains = ['*']
    start_urls = []
    pages = []
    pipeline = [CustomLinkPipeline]

    def __init__(self, links, **kwargs):
        array_links = links.split(',')
        self.start_urls = array_links
        super().__init__(**kwargs)

    def parse(self, response):
        yield {'text': get_text_from_element(html=response.text), 'url': response.url}
