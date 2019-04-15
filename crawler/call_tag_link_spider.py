from scrapy import cmdline

cmdline.execute("scrapy crawl TagLinkSpider -a links=https://www.hamptonroadslegal.com/bio/edrie-pfeiffer.cfm".split())
