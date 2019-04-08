from soleadify_ml.utils.SpiderUtils import check_spider_pipeline
import re


class SplashWebsitePipeline(object):

    @check_spider_pipeline
    def process_item(self, item, spider):
        print(item['text'])
