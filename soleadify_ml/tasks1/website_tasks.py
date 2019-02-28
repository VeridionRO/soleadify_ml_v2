from scrapy.crawler import CrawlerRunner
from scrapy import signals
from twisted.internet import reactor
from scrapy.utils.project import get_project_settings
from crawler.spiders.website_spider import WebsiteSpider
from soleadify_ml.celery import app
from celery import Task


class WebsiteContact(Task):
    name = 'extract-website-page-info'
    description = '''
    parse a website-page and extract a person:
    - name 
    - job title
    - email
    - phone
    '''
    public = True
    ignore_result = True
    website_id = None

    def run(self, website_id, *args, **kwargs):
        """
        trigger the command that crawles
        :param website_id:
        :param args:
        :param kwargs:
        :return:
        """

        def my_item_scrapped_handler(item, response, spider):
            print(item)
            self.update_state(state='PROGRESS')

        settings = get_project_settings()
        runner = CrawlerRunner(settings)
        d = runner.crawl(WebsiteSpider, website_id)
        d.addBoth(lambda _: reactor.stop())

        for crawler in runner.crawlers:
            crawler.signals.connect(my_item_scrapped_handler, signal=signals.item_scraped)

        reactor.run()


app.tasks.register(WebsiteContact())
