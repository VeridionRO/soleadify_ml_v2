from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://northerncoloradorentals.com/properties/?city=2&page=10".split())
