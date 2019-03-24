from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=5465466 -a force=True".split())
