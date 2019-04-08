import scrapy
from lxml import etree
from scrapy_splash import SplashRequest
import json
from crawler.pipelines.splash_website_pipeline import SplashWebsitePipeline

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(0.5))
  return {
    html = splash:html(),
    png = splash:png(),
  }
end
"""


class SplashWebsiteSpider(scrapy.Spider):
    name = 'SplashWebsiteSpider'
    start_urls = ["https://www.yellowpages.com/tampa-fl/attorneys"]
    pipeline = [SplashWebsitePipeline]
    allowed_domains = ['martindale.com']

    def start_requests(self):
        yield SplashRequest(
            "https://www.yellowpages.com/tampa-fl/attorneys", self.parse,
            endpoint='execute',
            cache_args=['lua_source'],
            args={
                'wait': 0.5,
                'html': 1,
                'lua_source': script,
                'png': 1,
            },
        )

    def parse(self, response):
        json_lds = response.selector.xpath('//script[@type="application/ld+json"]/text()').getall()

        for json_ld in json_lds:
            website_data = json.loads(json_ld)
            yield {'text': website_data}
