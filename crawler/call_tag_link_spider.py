from scrapy import cmdline

cmdline.execute("scrapy crawl TagLinkSpider -a link=https://www.highlandproperty.com.au/about-us/our-team/".split())
