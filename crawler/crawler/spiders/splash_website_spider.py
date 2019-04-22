import scrapy
from scrapy_splash import SplashRequest
from crawler.pipelines.splash_website_pipeline import SplashWebsitePipeline
from soleadify_ml.models.website import Website

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(0.5))
  return {
    html = splash:html(),
    png = splash:png()
  }
end
"""


class SplashWebsiteSpider(scrapy.Spider):
    name = 'SplashWebsiteSpider'
    pipeline = [SplashWebsitePipeline]
    website = None
    http_user = 'user'
    http_pass = 'userpass'

    def __init__(self, website_id, **kw):
        self.website = Website.objects.get(pk=website_id)

        super(SplashWebsiteSpider, self).__init__(**kw)

    def start_requests(self):
        if self.website and self.website.contact_state == 'pending':
            self.website.contact_state = 'working'
            self.website.save(update_fields=['contact_state'])

            yield SplashRequest(
                self.website.get_link(), self.parse,
                endpoint='execute',
                cache_args=['lua_source'],
                args={
                    'wait': 0.5,
                    'html': 1,
                    'lua_source': script,
                    'png': 1
                },
            )

    def parse(self, response):
        yield {'response': response, 'website': self.website}

    def close(self, spider):
        self.website.contact_state = 'finished'
        self.website.save(update_fields=['contact_state'])
