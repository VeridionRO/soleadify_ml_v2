import socket
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import logging

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from crawler.spiders.splash_website_spider import SplashWebsiteSpider
from soleadify_ml.utils.SocketUtils import recv_end, connect
from soleadify_ml.utils.LocationUtils import get_location

logger = logging.getLogger(__name__)


@csrf_exempt
def category(request):
    """
    get the category and text-language
    :param request:
    :return:
    """
    website_id = request.POST.get('website_id', '')
    # t1 = time.time()
    # logger.info(str(website_id) + ' - started category request!')
    # category socket
    soc_category = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc_category.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect(soc_category, '', 50008)

    text = request.POST.get('text', '')
    category_ids = []

    if text:
        try:
            soc_category.sendall(text.encode('utf8') + '--end--'.encode('utf8'))
            category_ids = json.loads(recv_end(soc_category))
        except:
            logger.info(str(website_id) + "error")

    soc_category.close()
    # t2 = time.time()
    # logger.info(str(website_id) + ' - ' + str(t2 - t1) + 'ended category request!')

    return HttpResponse(json.dumps(category_ids), content_type='application/json')


@csrf_exempt
def location(request):
    """
    get the location
    :param request:
    :return:
    """
    website_id = request.POST.get('website_id', 0)
    text = request.POST.get('text', '''
Park Cities/Dallas
8115 Preston Rd #270
Dallas, TX 75225
Phone: 214.692.8200
Fax: 214.692.8255
 
Collin County
By Appointment Only
5700 Granite Pkwy #200
Plano, TX 75024
Phone: 972.731.2501
 Green Initiative
Hablamos Español
We serve clients throughout Texas including those in the following localities: Dallas County including Dallas, Garland, Highland Park, Irving, Mesquite, Richardson, and University Park; Collin County including Allen, Frisco, McKinney, Murphy, Plano, and Prosper; Denton County including Carrollton, Denton, Lewisville, and Little Elm; Ector County including Odessa; Fort Bend County including Richmond and Sugar Land; Grayson County including Denison and Sherman; Harris County including Houston; Lamar County including Paris; Midland County including Midland; Rockwall County including Rockwall; Tarrant County including Colleyville, Fort Worth, and Southlake; Travis County including Austin; and Williamson County including Round Rock.''')
    country_code = request.POST.get('country_code', '')

    # t1 = time.time()

    soc_location = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc_location.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect(soc_location, '', 50006)
    website_location = None

    if text:
        try:
            website_location = get_location(soc_location, text, country_code)
        except Exception:
            logger.info(str(website_id) + "error")

    soc_location.close()

    # t2 = time.time()
    # logger.info(str(website_id) + ' - ' + str(t2 - t1))

    return HttpResponse(json.dumps(website_location), content_type='application/json')


@csrf_exempt
def testing(request):
    return HttpResponse(json.dumps(['a']), content_type='application/json')
