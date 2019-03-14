from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=http://www.cardinalcapital.us/social-services-team".split())
