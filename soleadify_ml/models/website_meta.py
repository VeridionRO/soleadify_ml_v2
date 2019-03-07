from django.db import models


class WebsiteMeta(models.Model):
    id = models.IntegerField(primary_key=True)
    website_id = models.IntegerField()
    meta_key = models.CharField(max_length=255)
    meta_value = models.CharField(max_length=255)
    count = models.IntegerField()

    class Meta:
        db_table = 'website_metas'
