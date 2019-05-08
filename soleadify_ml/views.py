import urllib.request
import socket
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import logging
import time

from soleadify_ml.utils.HTML2TextV2 import HTML2TextV2
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

    return HttpResponse(json.dumps(category_ids), content_type='application/json')


@csrf_exempt
def location(request):
    """
    get the location
    :param request:
    :return:
    """
    t1 = time.time()
    logger.info(str(t1))
    website_id = request.POST.get('website_id', 0)
    text = request.POST.get('text', '')
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

    t2 = time.time()
    logger.info(str(t2 - t1))

    return HttpResponse(json.dumps(website_location), content_type='application/json')


@csrf_exempt
def testing(request):
    response = urllib.request.urlopen('https://1800radiator.com/en-US/Home/ContactUs')
    html = response.read().decode('utf-8')

    converter = HTML2TextV2(bodywidth=0)
    converter.ignore_images = True
    converter.single_line_break = True
    converter.inheader = True
    converter.get_email_phone = True
    converter.emphasis_mark = ' '
    text = converter.handle(html)

    soc_location = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc_location.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connect(soc_location, '', 50006)

    website_location = get_location(soc_location, text, '')
    return HttpResponse(json.dumps(website_location), content_type='application/json')
