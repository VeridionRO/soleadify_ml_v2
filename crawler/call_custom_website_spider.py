from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://iremwi.com/sponsors.php".split())
