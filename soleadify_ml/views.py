import socket
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

from soleadify_ml.models.website_job import WebsiteJob
from soleadify_ml.utils.SocketUtils import recv_end, connect
from soleadify_ml.utils.LocationUtils import get_location
import logging

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

    # t2 = time.time()
    # logger.info(str(website_id) + ' - ' + str(t2 - t1))

    return HttpResponse(json.dumps(website_location), content_type='application/json')


@csrf_exempt
def testing(request):
    version = WebsiteJob.objects.get(pk=1)
    website = version.website
    # website_id = request.GET.get('website_id', 0)
    # website = Website.objects.get(pk=website_id)
    # a = website.website_job_set.all()
    print(website)

# @csrf_exempt
# def test(request):
#     phrase = 'this is a test'
#     phrase_parts = phrase.split()
#     return HttpResponse(json.dumps(phrase_parts), content_type='application/json')


# def test(request):
#     xml = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?><user></user>'''
#     if os.path.isfile('test.xml'):
#         with open('test.xml', 'r') as in_file:
#             xml = json.load(in_file)
#
#     return HttpResponse(xml, content_type='text/xml')
