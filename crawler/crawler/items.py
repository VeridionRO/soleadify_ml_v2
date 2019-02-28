from scrapy import Field
from soleadify_ml.models.website_page import WebsitePage
from scrapy_djangoitem import DjangoItem


class WebsitePageItem(DjangoItem):
    # fields for this item are automatically created from the django model
    django_model = WebsitePage
    text = Field()
    link = Field()
    response = Field()
