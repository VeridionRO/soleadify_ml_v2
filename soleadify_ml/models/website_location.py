from django.db import models


class WebsiteLocation(models.Model):
    id = models.IntegerField(primary_key=True)
    website_id = models.IntegerField()
    website_page_id = models.IntegerField()
    country_code = models.CharField(max_length=255)
    country_name = models.CharField(max_length=255)
    region_code = models.CharField(max_length=255)
    region_name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state_district = models.CharField(max_length=255)
    city_district = models.CharField(max_length=255)
    staircase = models.CharField(max_length=255)
    entrance = models.CharField(max_length=255)
    po_box = models.CharField(max_length=255)
    postcode = models.CharField(max_length=255)
    suburb = models.CharField(max_length=255)
    road = models.CharField(max_length=255)
    house_number = models.CharField(max_length=255)
    level = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    occurrences = models.IntegerField()

    # occurrences
    class Meta:
        db_table = 'website_locations'
