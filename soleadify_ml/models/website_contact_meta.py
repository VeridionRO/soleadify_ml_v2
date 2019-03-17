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

    def update_phone_value(self, country_codes=None):
        valid_phone = self.get_valid_country_phone(country_codes, self.meta_value)
        if valid_phone:
            self.meta_value = valid_phone

    @staticmethod
    def get_valid_country_phone(country_codes, phone_text):
        try:
            for country_code in country_codes:
                phone = phonenumbers.parse(phone_text, country_code)
                if phonenumbers.is_valid_number(phone):
                    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            pass

        return None
