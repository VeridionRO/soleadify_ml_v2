from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=7745985 -a force=True".split())
