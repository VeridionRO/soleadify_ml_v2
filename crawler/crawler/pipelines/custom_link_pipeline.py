import re
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline


class CustomLinkPipeline(object):

    @check_spider_pipeline
    def process_item(self, item, spider):
        url_strip = re.sub(r'[^a-zA-Z]+', '_', item['url'])

        with open('/Users/mihaivinaga/Work/soleadify_ml/soleadify_ml/files/' + url_strip, 'a') as the_file:
            the_file.write(item['text'])
