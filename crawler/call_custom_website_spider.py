from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.tpco.com/article.php?CNID=141".split())
