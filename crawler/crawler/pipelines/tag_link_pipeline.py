import logging
import re
import json

from soleadify_ml.utils.SocketUtils import recv_end
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline

logger = logging.getLogger('soleadify_ml')


class TagLinkPipeline(object):
    spacy_model = None

    @check_spider_pipeline
    def process_item(self, item, spider):
        link = item['link']
        docs = []

        try:
            spider.soc_spacy.sendall(item['text'].encode('utf8') + '--end--'.encode('utf8'))
            docs = json.loads(recv_end(spider.soc_spacy))
        except:
            logger.error("error")

        website_tags = {"content": item['text'], "annotation": [], "extras": None}

        for ent in docs:
            entity = {
                "label": [ent['label']],
                "points": [{"start": ent.start_char - 1, "end": ent.end_char - 2, "text": ent.text}]
            }
            website_tags["annotation"].append(entity)

        link = re.sub(r'[^a-zA-Z]+', '_', link)
        with open('/Users/mihaivinaga/Work/soleadify_ml/soleadify_ml/files/' + link, 'a') as the_file:
            the_file.write(json.dumps(website_tags))
        return website_tags
