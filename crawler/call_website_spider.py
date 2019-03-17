from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=7704327 -a force=True".split())
