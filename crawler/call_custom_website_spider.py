from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.sentrymgt.com/offices/atlanta-north/".split())
