from scrapy.crawler import CrawlerProcess

from crawler.spiders.splash_website_spider import SplashWebsiteSpider
from crawler.spiders.website_spider import WebsiteSpider
from soleadify_ml.celery import app

from billiard.context import Process
from scrapy.utils.project import get_project_settings


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
    def __init__(self, website_id, force=False):
        Process.__init__(self)
        settings = get_project_settings()
        self.crawler = CrawlerProcess(settings)
        self.website_id = website_id
        self.force = force

    def run(self):
        self.crawler.crawl(SplashWebsiteSpider, website_id=self.website_id, force=self.force)
        self.crawler.start()


class VersionWebsiteStarter(Process):
    def __init__(self, website_id, force=False):
        Process.__init__(self)
        self.website_id = website_id
        self.force = force

    def run(self):
        from soleadify_ml.models.website_version import WebsiteVersion
        WebsiteVersion.parse(self.website_id, self.force)


def run_website_spider(website_id):
    crawler = WebsiteSpiderStarter(website_id)
    crawler.start()
    crawler.join()


def run_splash_website_spider(website_id, force=False):
    crawler = SplashWebsiteSpiderStarter(website_id, force)
    crawler.start()
    crawler.join()


def run_website_version(website_id, force=False):
    crawler = VersionWebsiteStarter(website_id, force)
    crawler.start()
    crawler.join()


@app.task
def website_spider(website_id):
    return run_website_spider(website_id)


@app.task
def splash_website_spider(website_id, force=False):
    return run_splash_website_spider(website_id, force)


@app.task
def get_version(website_id, force):
    run_website_version(website_id, force)
