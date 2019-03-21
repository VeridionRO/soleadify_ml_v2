from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3288994 -a force=True".split())
