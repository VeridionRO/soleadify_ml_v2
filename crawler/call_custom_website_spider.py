from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.govbergrealty.com/meet-the-team/".split())
