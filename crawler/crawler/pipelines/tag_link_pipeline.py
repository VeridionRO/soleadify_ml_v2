from soleadify_ml.utils.SpiderUtils import check_spider_pipeline
import re


class TagLinkPipeline(object):

    @check_spider_pipeline
    def process_item(self, item, spider):
        doc = spider.spacy_model(item['text'])
        website_tags = {"content": item['text'], "annotation": [], "extras": None,
                        "metadata": {"first_done_at": 1552242586000, "last_updated_at": 1552249174000, "sec_taken": 0,
                                     "last_updated_by": "3BCYEQgDIHTFtTzwIy6Dpeowaae2", "status": "done",
                                     "evaluation": "NONE"}
                        }
        doc._.lines = [x.start() for x in re.finditer('\n', doc.text)]
        for ent in doc.ents:
            entity = {
                "label": [ent.label_],
                "points": [{"start": ent.start_char, "end": ent.end_char - 1, "text": ent.text}]
            }
            website_tags["annotation"].insert(0, entity)

        spider.tags.append(website_tags)
        return website_tags
