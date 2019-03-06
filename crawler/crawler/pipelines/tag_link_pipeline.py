import re
import json
from django.conf import settings
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline


class TagLinkPipeline(object):

    @check_spider_pipeline
    def process_item(self, item, spider):
        link = item['link']
        import spacy
        spacy_model = spacy.load(settings.SPACY_CUSTOMN_MODEL_FOLDER)
        doc = spacy_model(item['text'])
        website_tags = {"content": item['text'], "annotation": [], "extras": None}

        for ent in doc.ents:
            entity = {
                "label": [ent.label_],
                "points": [{"start": ent.start_char - 1, "end": ent.end_char, "text": ent.text}]
            }
            website_tags["annotation"].append(entity)

        link = re.sub(r'[^a-zA-Z]+', '_', link)
        with open('/Users/mihaivinaga/Work/soleadify_ml_v2/soleadify_ml/files/' + link, 'w') as the_file:
            the_file.write(json.dumps(website_tags))
        return website_tags
