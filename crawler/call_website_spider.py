from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3013404 -a force=True".split())
