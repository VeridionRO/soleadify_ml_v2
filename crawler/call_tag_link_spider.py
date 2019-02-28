from scrapy import cmdline

cmdline.execute("scrapy crawl TagLinkSpider -a link=https://www.melbournerealestate.com.au/agent/caitlin-okeeffe/".split())
