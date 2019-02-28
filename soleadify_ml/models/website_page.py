from django.db import models


class WebsitePage(models.Model):
    id = models.IntegerField(primary_key=True)
    page = models.CharField(max_length=255)
    website_id = models.IntegerField()
    # http_status = models.IntegerField()
    processed = models.IntegerField()
    # text = models.TextField()

    class Meta:
        db_table = 'website_pages'
