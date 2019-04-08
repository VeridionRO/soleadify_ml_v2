from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.martindale.com/organization/duane-morris-llp-190381/new-york-new-york-445139-f/".split())
