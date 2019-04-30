from scrapy.crawler import CrawlerProcess

from crawler.spiders.splash_website_spider import SplashWebsiteSpider
from crawler.spiders.website_spider import WebsiteSpider
from soleadify_ml.celery import app

from billiard.context import Process
from scrapy.utils.project import get_project_settings

from soleadify_ml.models.website_version import WebsiteVersion


class WebsiteSpiderStarter(Process):
    def __init__(self, website_id):
        Process.__init__(self)
        settings = get_project_settings()
        self.crawler = CrawlerProcess(settings)
        self.website_id = website_id

    def run(self):
        self.crawler.crawl(WebsiteSpider, self.website_id)
        self.crawler.start()


class SplashWebsiteSpiderStarter(Process):
    def __init__(self, website_id):
        Process.__init__(self)
        settings = get_project_settings()
        self.crawler = CrawlerProcess(settings)
        self.website_id = website_id

    def run(self):
        self.crawler.crawl(SplashWebsiteSpider, self.website_id)
        self.crawler.start()


def run_website_spider(website_id):
    crawler = WebsiteSpiderStarter(website_id)
    crawler.start()
    crawler.join()


def run_splash_website_spider(website_id):
    crawler = SplashWebsiteSpiderStarter(website_id)
    crawler.start()
    crawler.join()


@app.task
def website_spider(website_id):
    return run_website_spider(website_id)


@app.task
def splash_website_spider(website_id):
    return run_splash_website_spider(website_id)


@app.task
def get_version(website_id):
    return WebsiteVersion.parse(website_id)
