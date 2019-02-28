import json
from django.db import models
import pandas as pd
from soleadify_ml.models.category import Category
from soleadify_ml.utils import MLUtils
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from django.db.models.functions import Length


class CategoryWebsiteText(models.Model):
    id = models.IntegerField(primary_key=True)
    category_id = models.IntegerField()
    website_id = models.IntegerField()
    page_text = models.TextField()

    class Meta:
        db_table = 'category_website_texts'

    @staticmethod
    def load_ml_data():
        """
        load data from the database and return a pandas data-frame
        :return:
        """
        model_text = []
        category_ids = Category.objects. \
            values_list('id'). \
            exclude(id__in=[10419, 10416])
        for category in category_ids.iterator():
            # parked websites
            category_id = category[0]
            print(category_id)
            db_texts = CategoryWebsiteText.objects. \
                filter(category_id=category_id). \
                values_list('category_id', 'page_text'). \
                order_by(Length('page_text').desc())
            if category_id != 10010:
                db_texts = db_texts.all()[:3000]

            category_websites = sum(1 for _ in db_texts.iterator())
            if category_websites > 150:
                for db_text in db_texts.iterator():
                    model_text.append(db_text)
                    pass
                print(category_id)
                print(category_websites)

        df = pd.DataFrame(model_text, columns=['category_id', 'page_text'])

        return df

    @staticmethod
    def load_keywords():
        """
        load top keywords for each category
        :return:
        """
        category_keywords = {}
        category_texts_cached = {}
        model_text = []
        category_ids = Category.objects. \
            values_list('id'). \
            exclude(id__in=[10419, 10416, 10010, 10011]).all()
        for category in category_ids.iterator():
            category_id = category[0]
            category_texts = CategoryWebsiteText.category_text(category_id)
            if len(category_texts) == 0:
                continue

            model_text.extend(category_texts)
            category_texts_cached[category_id] = category_texts

        count_vect = CountVectorizer(min_df=5, max_df=0.3, ngram_range=(1, 2), stop_words=MLUtils.stop_words(),
                                     max_features=50000)
        print('fit_transform')
        model_text_counts = count_vect.fit_transform(model_text)
        tf_idf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
        print('fit')
        tf_idf_transformer.fit(model_text_counts)

        # you only needs to do this once, this is a mapping of index to
        feature_names = count_vect.get_feature_names()

        for category_id, category_texts in category_texts_cached.items():
            category_text = ' '.join(category_texts)

            # generate tf-idf for the given document
            tf_idf_vector = tf_idf_transformer.transform(count_vect.transform([category_text]))

            # sort the tf-idf vectors by descending order of scores
            sorted_items = MLUtils.sort_coo(tf_idf_vector.tocoo())

            # extract only the top n; n here is 20
            keywords = MLUtils.extract_topn_from_vector(feature_names, sorted_items, 20)
            category_keywords[category_id] = keywords

        return category_keywords

    @staticmethod
    def category_text(category_id, website_no_limit = 3000):
        """
        get the entire text of a category
        :param category_id:
        :return:
        """
        category_texts = []
        db_texts = CategoryWebsiteText.objects. \
                       filter(category_id=category_id). \
                       values_list('page_text').order_by(Length('page_text').desc()).all()[:3000]

        category_websites = sum(1 for _ in db_texts.iterator())

        if category_websites > 150:
            print(category_id)
            for db_text in db_texts.iterator():
                category_texts.append(db_text[0])

        return category_texts
