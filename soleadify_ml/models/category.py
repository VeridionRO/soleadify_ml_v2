from django.db import models
import pandas as pd


class Category(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    parent_id = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'categories'

    @staticmethod
    def load_ml_data():
        """
        load data from the database and return a pandas dataframe
        :return:
        """
        model_text = []
        categories = Category.objects. \
            values_list('id', 'name')
        for db_text in categories.iterator():
            model_text.append(db_text)
            pass

        df = pd.DataFrame(model_text, columns=['id', 'category'])

        return df
