from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.acfls.org/presenter/ron-brot-j-d/".split())
