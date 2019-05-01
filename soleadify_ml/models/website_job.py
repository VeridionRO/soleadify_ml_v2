from django_mysql.models import EnumField
from django.db import models

from soleadify_ml.models.website import Website


class WebsiteJob(models.Model):
    id = models.AutoField(primary_key=True)
    job_type = models.IntegerField()
    status = EnumField(choices=['unprocessed', 'pending', 'working', 'finished', 'error'])
    website = models.ForeignKey(Website, on_delete=models.CASCADE)

    class Meta:
        db_table = 'website_jobs'
