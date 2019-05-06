import json
import os
import time
from urllib.error import URLError

import requests
import gzip
import urllib.request
import logging

from io import BytesIO
from isoweek import Week
from django.db import models
from soleadify_ml import settings
from json import JSONDecodeError

from soleadify_ml.models.website import Website
from soleadify_ml.models.website_job import WebsiteJob

logger = logging.getLogger(__name__)


class WebsiteVersion(models.Model):
    id = models.AutoField(primary_key=True)
    website_id = models.IntegerField()
    version_date = models.DateField()
    modifications = models.IntegerField()
    index = []
    index_dates = {
        'CC-MAIN-2012': '2012-01-01',
        'CC-MAIN-2009-2010': '2010-01-01',
        'CC-MAIN-2008-2009': '2009-01-01',
    }

    class Meta:
        db_table = 'website_versions'

    @staticmethod
    def parse(website_id, force=False):
        versions = []
        indexes = []
        existing_pages = {}
        website = Website.objects.get(pk=website_id)
        error_count = 0

        if not website:
            return None

        version_job = website.version_job()
        if version_job and version_job.status != 'pending' and not force:
            return []
        elif not version_job:
            version_job = WebsiteJob(
                website_id=website.id,
                job_type=Website.VERSION_JOB_TYPE,
                status='working'
            )
            version_job.save()

        if len(WebsiteVersion.index) == 0:
            WebsiteVersion.get_indexes()

        for index in WebsiteVersion.index:
            if error_count >= 3:
                break

            text = ''
            retry = 0
            index_list = []
            logger.debug("website: %s, index: %s" % (website.id, index))
            url = '%s%s-index?url=%s*&output=json' % (settings.COMMON_CRAWL_SERVER, index, website.get_domain())
            while True:
                try:
                    response = urllib.request.urlopen(url)
                    text = response.read().decode('utf-8')
                    break
                except urllib.request.HTTPError as e:
                    logger.error("website: %s, index: %s, error: %s" % (website.id, index, e))
                    error_count += 1
                    retry += 1
                except URLError as e:
                    # os.system('/etc/anaconda3/bin/wayback -t 5 -d /var/www/cc-index-server/ > '
                    #           '/var/www/cc-index-server/info.log')
                    logger.error("website: %s, index: %s, error: %s" % (website.id, index, e))
                    retry += 1

                if retry >= 2:
                    break
                elif retry >= 1:
                    logger.error("website: %s, index: %s, message: sleeping" % (website.id, index))
                    time.sleep(20)

            page_strings = text.split('\n')
            for page_string in page_strings:
                try:
                    page = json.loads(page_string)

                    if int(page['length']) < 1000:
                        continue

                    index_list.append({
                        'filename': page['filename'],
                        'length': page['length'],
                        'offset': page['offset'],
                        'urlkey': page['urlkey'],
                    })
                except JSONDecodeError:
                    continue
            indexes.append((index, index_list))

        indexes.reverse()
        for index_key, index_list in indexes:
            date = WebsiteVersion.get_date_from_index(index_key)
            try:
                version = WebsiteVersion.check_versions(index_list, existing_pages, website, date)
                if version:
                    versions.append(version)
            except IndexError:
                pass

        WebsiteVersion.objects.bulk_create(versions, ignore_conflicts=True)
        version_job.status = 'finished'
        version_job.save()

        return versions

    @staticmethod
    def check_versions(current_version, existing_pages, website, date):
        count = 0
        for page in current_version:
            length = int(page['length'])
            url_key = page['urlkey']

            if url_key in existing_pages:
                length_v1 = existing_pages[url_key]
                if abs(length_v1 - length) >= 500:
                    count += 1
            elif url_key not in existing_pages:
                count += 1
            existing_pages[url_key] = length

        return WebsiteVersion(website_id=website.id, version_date=date, modifications=count) if count else None

    @staticmethod
    def download_page(record, index):
        offset, length = int(record['offset']), int(record['length'])
        offset_end = offset + length - 1

        # We'll get the file via HTTPS so we don't need to worry about S3 credentials
        # Getting the file on S3 is equivalent however - you can request a Range
        prefix = 'https://commoncrawl.s3.amazonaws.com/'

        # We can then use the Range header to ask for just this set of bytes
        resp = requests.get(prefix + record['filename'], headers={'Range': 'bytes={}-{}'.format(offset, offset_end)})

        # The page is stored compressed (gzip) to save space
        # We can extract it using the GZIP library
        raw_data = BytesIO(resp.content)
        f = gzip.GzipFile(fileobj=raw_data)

        # What we have now is just the WARC response, formatted:
        data = f.read().decode()

        response = ""

        if len(data):
            try:
                warc, header, response = data.strip().split('\r\n\r\n', 2)
            except:
                pass

        if record['urlkey'] == '':
            with open('/Users/mihaivinaga/Work/soleadify_ml_v2/soleadify_ml/files/' + index, 'a') as the_file:
                the_file.write(response)

        return response

    @staticmethod
    def get_indexes():
        index_url = '%s%s' % (settings.COMMON_CRAWL_SERVER, 'collinfo.json')
        previous_year = None
        try:
            response = urllib.request.urlopen(index_url)
            text = response.read().decode('utf-8')
            indexes = json.loads(text)
        except urllib.request.HTTPError:
            return []
        except URLError:
            os.system('/etc/anaconda3/bin/wayback -t 5 -d /var/www/cc-index-server/ > '
                      '/var/www/cc-index-server/info.log')
            return []

        for index in indexes:
            year = WebsiteVersion.get_date_from_index(index['id'], '%Y')
            if len(WebsiteVersion.index) < 24:
                WebsiteVersion.index.append(index['id'])
            elif previous_year != year:
                WebsiteVersion.index.append(index['id'])
            previous_year = year

    @staticmethod
    def get_date_from_index(index, date_format='%Y-%m-%d'):
        if index in WebsiteVersion.index_dates:
            date = WebsiteVersion.index_dates[index]
        else:
            dirty_date = index.replace('CC-MAIN-', '')
            dirty_date_parts = dirty_date.split('-')
            year = int(dirty_date_parts[0])
            week_no = int(dirty_date_parts[1])
            week_date = Week(year, week_no).monday()
            date = week_date.strftime(date_format)
        return date
