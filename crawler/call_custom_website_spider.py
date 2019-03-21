from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=http://www.pittardlaw.com/index.html".split())
