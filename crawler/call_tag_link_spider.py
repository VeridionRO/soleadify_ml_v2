from scrapy import cmdline

cmdline.execute("scrapy crawl TagLinkSpider -a links=https://www.33rdcompany.com/news-and-events/the-process-of-evicting-a-tenant-in-minnesota-property-management-advice".split())
