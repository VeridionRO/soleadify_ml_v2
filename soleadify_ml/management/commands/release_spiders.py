from django.core.management.base import BaseCommand
from scrapy.utils.project import get_project_settings
from crawler.spiders.website_spider import WebsiteSpider
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor


class Command(BaseCommand):
    help = "Unleash the army of spiders upon the website!!!"

    def add_arguments(self, parser):
        parser.add_argument('-w', '--website_id', metavar='N', type=int, nargs='+',
                            help='Indicates the website-id to be crawler', default=4885276)

    def handle(self, *args, **options):
        website_id = options['website_id']
        runner = CrawlerRunner(get_project_settings())
        d = runner.crawl(WebsiteSpider, website_id)
        d.addBoth(lambda _: self.handle(runner))
        reactor.run()