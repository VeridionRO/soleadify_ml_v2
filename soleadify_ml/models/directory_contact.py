from django.db import models


class DirectoryContact(models.Model):
    id = models.IntegerField(primary_key=True)
    law_cat = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    workplace = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    organization_key = models.CharField(max_length=255)
    done = models.IntegerField()

    class Meta:
        db_table = 'directory_contact'
