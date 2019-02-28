from django.db import models
import phonenumbers
from phonenumbers import NumberParseException


class WebsiteContactMeta(models.Model):
    models.AutoField(primary_key=True)
    website_contact_id = models.IntegerField()
    meta_key = models.CharField(max_length=255)
    meta_value = models.CharField(max_length=255)
    page = models.CharField(max_length=1024)

    class Meta:
        db_table = 'website_contact_metas'

    def update_phone_value(self, country_code=None):
        if self.meta_key == 'PHONE':
            try:
                phone = phonenumbers.parse(self.meta_value, country_code)
                if phonenumbers.is_valid_number(phone):
                    self.meta_value = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            except NumberParseException:
                pass
