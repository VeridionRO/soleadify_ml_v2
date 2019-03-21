from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://alexanderlaw.com/library-piwd-14".split())
