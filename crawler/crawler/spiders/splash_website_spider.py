import scrapy
import logging
from scrapy_splash import SplashRequest
from crawler.pipelines.splash_website_pipeline import SplashWebsitePipeline
from soleadify_ml.models.website import Website
from soleadify_ml.models.website_job import WebsiteJob

logger = logging.getLogger('soleadify_ml')

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))
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
    force = False

    def __init__(self, website_id=None, force=False, **kw):
        self.website = Website.objects.get(pk=website_id)
        self.splash_job = self.website.splash_job()
        self.force = force

        super(SplashWebsiteSpider, self).__init__(**kw)

    def start_requests(self):

        if self.splash_job and self.splash_job.status != 'pending':
            logger.debug('already processed: ' + str(self.website.id))
            return
        elif not self.splash_job:
            self.splash_job = WebsiteJob(
                website_id=self.website.id,
                job_type=Website.SPLASH_JOB_TYPE,
                status='working'
            )
            self.splash_job.save()
        else:
            self.splash_job.status = 'working'
            self.splash_job.save()

        if self.website.has_s3_file() and not self.force:
            return

        yield SplashRequest(
            self.website.get_link(), self.parse,
            endpoint='execute',
            cache_args=['lua_source'],
            args={
                'wait': 2,
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
