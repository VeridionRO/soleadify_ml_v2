import boto3
from django.core.management.base import BaseCommand
from lxml import etree


class Command(BaseCommand):
    help = "Add to queue"
    s3_client = None

    def handle(self, *args, **options):
        s3 = boto3.resource('s3')
        my_bucket = s3.Bucket('irs-form-990')

        for obj in my_bucket.objects.all():
            root = etree.fromstring(obj.get()['Body'].read().decode('utf-8'))
            businesses = root.xpath('//irs:PreparerFirmBusinessName', namespaces={'irs': 'http://www.irs.gov/efile'})
            websites = root.xpath('//irs:WebSite', namespaces={'irs': 'http://www.irs.gov/efile'})
            addresses = root.xpath('//irs:USAddress', namespaces={'irs': 'http://www.irs.gov/efile'})

            for business in businesses:
                print(business.tag, business.text)

            for website in websites:
                print(website.tag, website.text)

            for address in addresses:
                print(address.tag, address.text)

            print(root)
