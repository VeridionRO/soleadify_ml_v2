from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.highlandproperty.com.au/about-us/our-team/peter-cox/1278/".split())
