from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.tempopropertiesinc.com/meet-our-team/".split())
