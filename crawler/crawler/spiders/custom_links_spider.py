import scrapy

from crawler.pipelines.custom_link_pipeline import CustomLinkPipeline
from crawler.spiders.spider_common import SpiderCommon


class CustomLinksSpider(scrapy.Spider, SpiderCommon):
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
        yield {'text': self.get_text_from_element(html=response.text), 'url': response.url}
