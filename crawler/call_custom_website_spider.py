from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=http://pagepearce.com.au/members/david-bishop/".split())
