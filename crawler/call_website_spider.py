from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3012732 -a force=True".split())
