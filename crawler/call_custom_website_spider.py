from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://madecomfy.com.au/about-us/meet-the-team/".split())
