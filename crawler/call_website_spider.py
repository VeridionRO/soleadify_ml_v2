from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3014364 -a force=True".split())
