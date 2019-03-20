from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://newsouthprop.com/our-team/".split())
