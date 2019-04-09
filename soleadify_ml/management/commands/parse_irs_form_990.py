from tqdm import tqdm
import boto3
import csv
import json
from django.core.management.base import BaseCommand
from lxml import etree


class Command(BaseCommand):
    help = "Add to queue"
    s3_client = None

    def handle(self, *args, **options):
        s3 = boto3.resource('s3')
        with open('/Users/mihaivinaga/Work/soleadify_ml_v2/index_2018.json') as json_file:
            data = json.load(json_file)

        progress_bar = tqdm(desc="Processing", total=len(data['Filings2018']))

        with open('/Users/mihaivinaga/Work/soleadify_ml_v2/ngo.csv', 'w') as writeFile:

            writer = csv.writer(writeFile)

            for item in data['Filings2018']:
                obj = s3.Object('irs-form-990', item['ObjectId'] + '_public.xml')
                root = etree.fromstring(obj.get()['Body'].read())
                businesses = root.xpath('//irs:Filer/irs:BusinessName', namespaces={'irs': 'http://www.irs.gov/efile'})
                websites = root.xpath('//irs:WebSite', namespaces={'irs': 'http://www.irs.gov/efile'})
                website_address = root.xpath('//irs:WebsiteAddress', namespaces={'irs': 'http://www.irs.gov/efile'})
                website_address_txt = root.xpath('//irs:WebsiteAddressTxt', namespaces={'irs': 'http://www.irs.gov/efile'})
                addresses = root.xpath('//irs:USAddress', namespaces={'irs': 'http://www.irs.gov/efile'})
                description_tags = root.xpath('//irs:ActivityOrMissionDesc', namespaces={'irs': 'http://www.irs.gov/efile'})
                desc_tags = root.xpath('//irs:Desc', namespaces={'irs': 'http://www.irs.gov/efile'})
                mission_desc_tags = root.xpath('//irs:MissionDesc', namespaces={'irs': 'http://www.irs.gov/efile'})

                business_name = ''
                website_string = None
                city = None
                state = None
                zip_code = None
                description1 = None
                description2 = None
                description3 = None

                for business in businesses:
                    for child in business.getchildren():
                        business_name += child.text + ' '

                for website in website_address_txt:
                    website_string = website.text

                for description_tag in description_tags:
                    description1 = description_tag.text

                for desc_tag in desc_tags:
                    description2 = desc_tag.text

                for mission_desc_tag in mission_desc_tags:
                    description3 = mission_desc_tag.text

                if not website_address:
                    for website in websites:
                        website_string = website.text

                if not website_address:
                    for website in website_address:
                        website_string = website.text

                for address in addresses:
                    for child in address.getchildren():
                        if 'City' in child.tag:
                            city = child.text
                        if 'State' in child.tag:
                            state = child.text
                        if 'ZIPCd' in child.tag:
                            zip_code = child.text

                ngo_dict = {
                    'business_name': business_name,
                    'website': website_string,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code,
                    'description1': description1,
                    'description2': description2,
                    'description3': description3,
                }

                writer.writerow(ngo_dict.values())

                progress_bar.update(1)

        progress_bar.close()
