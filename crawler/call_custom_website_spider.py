from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.summitbunbury.com.au/about-us/".split())
