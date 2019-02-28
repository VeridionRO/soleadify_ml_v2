from threading import Thread

from scrapy.crawler import CrawlerProcess
from crawler.spiders.website_spider import WebsiteSpider
from soleadify_ml.celery import app

from billiard.context import Process
from scrapy.utils.project import get_project_settings


class UrlCrawlerScript(Process):
    def __init__(self, website_id):
        Process.__init__(self)
        settings = get_project_settings()
        self.crawler = CrawlerProcess(settings)
        self.website_id = website_id

    def run(self):
        self.crawler.crawl(WebsiteSpider, self.website_id)
        self.crawler.start()


def run_spider(website_id):
    # crawler = UrlCrawlerScript(website_id)
    # crawler.start()
    # crawler.join()
    process = CrawlerProcess(get_project_settings())
    process.crawl(WebsiteSpider, website_id)
    Thread(target=process.start).start()


@app.task
def scrapping(website_id):
    return run_spider(website_id)
