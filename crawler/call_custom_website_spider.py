from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=http://www.goodwintx.com/".split())
