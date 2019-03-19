from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3158223 -a force=True".split())
