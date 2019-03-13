from scrapy import cmdline

cmdline.execute("scrapy crawl WebsiteSpider -a website_id=3085326 -a force=True".split())
