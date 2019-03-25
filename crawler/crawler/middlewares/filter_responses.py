import re
import logging
from scrapy.exceptions import IgnoreRequest

logger = logging.getLogger('soleadify_ml')


class FilterResponses(object):
    """Limit the HTTP response types that Scrapy dowloads."""

    @staticmethod
    def is_valid_response(type_whitelist, content_type_header):
        for type_regex in type_whitelist:
            if re.search(type_regex, content_type_header):
                return True
        return False

    def process_response(self, request, response, spider):
        """
        Only allow HTTP response types that that match the given list of
        filtering regexs
        """
        type_whitelist = (r'text',)
        content_type_header = response.headers.get('content-type', None)
        if not content_type_header or not type_whitelist:
            return response

        content_type_header = content_type_header.decode("utf-8")

        if self.is_valid_response(type_whitelist, content_type_header):
            return response
        else:
            msg = "Ignoring request {}, content-type was not in whitelist".format(response.url)
            logger.error(msg)
            raise IgnoreRequest()
