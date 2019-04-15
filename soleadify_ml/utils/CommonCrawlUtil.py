import requests
from io import BytesIO
import gzip
import urllib.request
import json
from json import JSONDecodeError


class CommonCrawlUtil:
    website = None
    existing_pages = {}
    index = ['CC-MAIN-2017-04', 'CC-MAIN-2017-09', 'CC-MAIN-2017-13', 'CC-MAIN-2017-17', 'CC-MAIN-2017-22',
             'CC-MAIN-2017-26', 'CC-MAIN-2017-30', 'CC-MAIN-2017-34', 'CC-MAIN-2017-39', 'CC-MAIN-2017-43',
             'CC-MAIN-2017-47', 'CC-MAIN-2017-51', 'CC-MAIN-2018-05', 'CC-MAIN-2018-09', 'CC-MAIN-2018-13',
             'CC-MAIN-2018-17', 'CC-MAIN-2018-22', 'CC-MAIN-2018-26', 'CC-MAIN-2018-30', 'CC-MAIN-2018-34',
             'CC-MAIN-2018-39', 'CC-MAIN-2018-43', 'CC-MAIN-2018-47', 'CC-MAIN-2018-51', 'CC-MAIN-2019-04',
             'CC-MAIN-2019-09', 'CC-MAIN-2019-13']

    def __init__(self, website):
        self.website = website

    def parse(self):
        website_versions = []
        diffs = {}
        for index in CommonCrawlUtil.index:
            url = 'http://116.203.46.118:8080/%s-index?url=%s*&output=json' % (index, self.website.domain)
            try:
                response = urllib.request.urlopen(url)
                text = response.read().decode('utf-8')
            except urllib.request.HTTPError:
                continue
            page_strings = text.split('\n')
            website_version = {'index': index}

            for page_string in page_strings:
                try:
                    page = json.loads(page_string)

                    if int(page['length']) < 1000:
                        continue

                    page_version = {
                        'filename': page['filename'],
                        'length': page['length'],
                        'status': page['status'],
                        'offset': page['offset'],
                        'index': index,
                    }
                    website_version[page['urlkey']] = page_version

                except JSONDecodeError:
                    pass

            try:
                self.check_versions(website_version, diffs)
            except IndexError:
                pass

            for page_key, page_version in website_version.items():
                if 'length' in page_version:
                    self.existing_pages[page_key] = int(page_version['length'])

            website_versions.append(website_version)

        return diffs

    def check_versions(self, current_version, diffs):
        index = current_version['index']
        for page_key, page in current_version.items():
            if type(page) is not dict:
                continue

            length = int(page['length'])

            if page_key in self.existing_pages:
                length_v1 = self.existing_pages[page_key]
                if length == length_v1:
                    continue
                elif abs(length_v1 - length) > 500:
                    if index not in diffs:
                        diffs[index] = []

                    diffs[index].append({'page_key': page_key, 'diff': abs(length_v1 - length),
                                         'length': length, 'length_v1': length_v1})
            elif page_key not in self.existing_pages:
                if index not in diffs:
                    diffs[index] = []
                diffs[index].append({'page_key': page_key, 'diff': 0, 'length': length})

    def download_page(self, record):
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

        return response
