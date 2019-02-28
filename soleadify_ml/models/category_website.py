import json
from django.db import models
import pandas as pd
from soleadify_ml.models.category import Category
from soleadify_ml.utils import MLUtils
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from django.db.models.functions import Length


class CategoryWebsite(models.Model):
    category_id = models.IntegerField()
    website_id = models.IntegerField()

    class Meta:
        db_table = 'category_websites'
