from scrapy import cmdline

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.lexisnexis.com.au/en/insights-and-analysis/authors-and-experts/adrian-coorey".split())
