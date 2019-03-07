from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.pmiboise.com/wordpress/index.php/2018/04/".split())
