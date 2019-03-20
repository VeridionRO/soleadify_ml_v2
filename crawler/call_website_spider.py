from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=6000756 -a force=True".split())
