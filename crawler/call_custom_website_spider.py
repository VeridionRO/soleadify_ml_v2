from scrapy import cmdline
from soleadify_ml.utils.SpiderUtils import check_email

check_email('gga@argionislaw.com')

cmdline.execute("scrapy crawl CustomWebsiteSpider -a link=https://www.injurylawyershotline.com/Rafael_2395938.vcf".split())
