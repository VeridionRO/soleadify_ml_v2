from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3009484 -a force=True".split())
