import base64
from io import BytesIO
import boto3
from PIL import Image
import io

from soleadify_ml.utils.SpiderUtils import check_spider_pipeline


class SplashWebsitePipeline(object):

    @check_spider_pipeline
    def process_item(self, item, spider):
        response = item['response']
        website = item['website']
        titles = response.selector.xpath('//title/text()').getall()
        if len(titles) < 1:
            titles = response.selector.xpath('//meta[@property="og:title"]/@content').getall()

        title = '. '.join(titles)

        img_data = base64.b64decode(response.data['png'])
        basewidth = 400
        img = Image.open(BytesIO(img_data))
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        rgb_im = img.convert('RGB')

        s3 = boto3.resource('s3')

        rgb_im.save('some_image.jpg')

        output = io.BytesIO()
        rgb_im.save(output, format='JPEG')

        s3.Bucket('websites-ss').put_object(Key='%s/%s.jpg' % (website.get_id_path(), str(website.id)),
                                            Body=output.getvalue(), ContentType='image/jpeg')
        output.close()
        print(title)
