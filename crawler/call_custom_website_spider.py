from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=http://361realestate.com.au/Agent/Detail?agentId=836".split())
