import base64
from io import BytesIO
import boto3
from PIL import Image
import io

from soleadify_ml.models.website_meta import WebsiteMeta
from soleadify_ml.utils.SpiderUtils import check_spider_pipeline


class SplashWebsitePipeline(object):
    response = None
    website = None
    s3 = None

    @check_spider_pipeline
    def process_item(self, item, spider):
        self.response = item['response']
        self.website = item['website']

        jpeg_object = self.get_ss()

        title = self.get_title()
        description = self.get_description()
        meta_values = []

        if title:
            meta_values.append(WebsiteMeta(website_id=self.website.id, meta_key='title', meta_value=title))
        if description:
            WebsiteMeta(website_id=self.website.id, meta_key='description', meta_value=description)
        WebsiteMeta.objects.bulk_create(meta_values, ignore_conflicts=True)

        s3 = boto3.resource('s3')
        s3_path = '%s/%s.jpg' % (self.website.get_id_path(), str(self.website.id))
        s3.Bucket('websites-ss').put_object(Key=s3_path, Body=jpeg_object.getvalue(), ContentType='image/jpeg')

    def get_title(self):
        titles = self.response.selector.xpath('//title/text()').getall()
        if len(titles) < 1:
            titles = self.response.selector.xpath('//meta[@property="og:title"]/@content').getall()

        return '. '.join(titles).strip()

    def get_description(self):
        descriptions = self.response.selector.xpath('//meta[@name="description"]/@content').getall()
        if len(descriptions) < 1:
            descriptions = self.response.selector.xpath('//meta[@property="og:description"]/@content').getall()

        return '. '.join(descriptions).strip()

    def get_ss(self):
        img_data = base64.b64decode(self.response.data['png'])
        resize_width = 400
        img = Image.open(BytesIO(img_data))
        width_percent = (resize_width / float(img.size[0]))
        height_size = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((resize_width, height_size), Image.ANTIALIAS)
        rgb_im = img.convert('RGB')

        rgb_im.save('some_image.jpg')

        jpeg_object = io.BytesIO()
        rgb_im.save(jpeg_object, format='JPEG')

        return jpeg_object
