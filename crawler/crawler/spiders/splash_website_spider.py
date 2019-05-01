import scrapy
from scrapy_splash import SplashRequest
from crawler.pipelines.splash_website_pipeline import SplashWebsitePipeline
from soleadify_ml.models.website import Website
from soleadify_ml.models.website_job import WebsiteJob

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
    splash_job = None
    http_user = 'user'
    http_pass = 'userpass'

    def __init__(self, website_id, **kw):
        self.website = Website.objects.get(pk=website_id)
        self.splash_job = self.website.splash_job()
        super(SplashWebsiteSpider, self).__init__(**kw)

    def start_requests(self):
        if not self.website.has_s3_file():
            return
        if self.splash_job and self.splash_job.status == 'pending':
            return
        elif not self.splash_job:
            self.splash_job = WebsiteJob(
                website_id=self.website.id,
                job_type=Website.SPLASH_JOB_TYPE,
                status='working'
            )
            self.splash_job.save()

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
        self.splash_job.status = 'finished'
        self.splash_job.save()

    def spider_error(self, failure, response, spider):
        pass
