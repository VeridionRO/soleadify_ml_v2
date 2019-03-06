from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://traddcommercial.com/executive-team/".split())
