from django.db import models


class WebsiteDirector(models.Model):
    id = models.IntegerField(primary_key=True)
    organization_key = models.CharField(max_length=1024)
    website_id = models.IntegerField()

    class Meta:
        db_table = 'website_director'
