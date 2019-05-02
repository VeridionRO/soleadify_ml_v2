import json
import os
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

    class Meta:
        db_table = 'website_versions'

    @staticmethod
    def parse(website_id):
        versions = []
        existing_pages = {}
        website = Website.objects.get(pk=website_id)

        if not website:
            return None

        version_job = website.version_job()
        if version_job and version_job.status != 'pending':
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
            logger.debug("website: %s, index: %s" % (website.id, index))
            url = '%s%s-index?url=%s*&output=json' % (settings.COMMON_CRAWL_SERVER, index, website.domain)
            try:
                response = urllib.request.urlopen(url)
                text = response.read().decode('utf-8')
            except urllib.request.HTTPError as e:
                logger.error("website: %s, index: %s, error: %s" % (website.id, index, e))
                continue
            except urllib.error.URLError as e:
                os.system('/etc/anaconda3/bin/wayback -t 5 -d /var/www/cc-index-server/ > '
                          '/var/www/cc-index-server/info.log')
                logger.error("website: %s, index: %s, error: %s" % (website.id, index, e))
                continue
            page_strings = text.split('\n')
            website_version = {'index': index}

            for page_string in page_strings:
                try:
                    page = json.loads(page_string)

                    if int(page['length']) < 1000:
                        continue

                    website_version[page['urlkey']] = {
                        'filename': page['filename'],
                        'length': page['length'],
                        'status': page['status'],
                        'offset': page['offset'],
                        'index': index,
                    }
                except JSONDecodeError:
                    pass

            try:
                version = WebsiteVersion.check_versions(website_version, existing_pages, website)
                if version:
                    versions.append(version)
            except IndexError:
                pass

            for page_key, page_version in website_version.items():
                if 'length' in page_version:
                    existing_pages[page_key] = int(page_version['length'])

        WebsiteVersion.objects.bulk_create(versions, ignore_conflicts=True)
        version_job.status = 'finished'
        version_job.save()

        return versions

    @staticmethod
    def check_versions(current_version, existing_pages, website):
        index = current_version['index']
        dirty_date = index.replace('CC-MAIN-', '')
        dirty_date_parts = dirty_date.split('-')
        year = int(dirty_date_parts[0])
        week_no = int(dirty_date_parts[1])

        week_date = Week(year, week_no).monday()
        date = week_date.strftime('%Y-%m-%d')

        count = 0
        for page_key, page in current_version.items():
            if type(page) is not dict:
                continue

            length = int(page['length'])

            if page_key in existing_pages:
                length_v1 = existing_pages[page_key]
                if abs(length_v1 - length) <= 500:
                    continue
                else:
                    count += 1
            elif page_key not in existing_pages:
                count += 1

        return WebsiteVersion(website_id=website.id, version_date=date, modifications=count) if count else None

    @staticmethod
    def download_page(record):
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

        # if record['urlkey'] == 'com,jfdental)/':
        #     html = WebsiteVersion.download_page(record)
        #     with open('/Users/mihaivinaga/Work/soleadify_ml_v2/soleadify_ml/files/' + record['filename'],
        #               'a') as the_file:
        #         the_file.write(html)

        return response

    @staticmethod
    def get_indexes():
        index_url = '%s%s' % (settings.COMMON_CRAWL_SERVER, 'collinfo.json')
        indexes = []
        try:
            response = urllib.request.urlopen(index_url)
            text = response.read().decode('utf-8')
            indexes = json.loads(text)
        except urllib.request.HTTPError:
            pass

        for index in indexes:
            if len(WebsiteVersion.index) > 24:
                break
            WebsiteVersion.index.append(index['id'])

        WebsiteVersion.index.reverse()
