# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')

from news.radikal import Radikal
from news.cumhuriyet import Cumhuriyet
from news.t24 import T24
from news.milliyet import Milliyet

crawl_sites = {Milliyet}
#crawl_sites = {Milliyet, Radikal, T24, Cumhuriyet}


class TrNewsSpider(CrawlSpider):
    name = "trnews"
    allowed_domains = []
    start_urls = ()
    rules = ()
    rules_allow = []
    rules_deny = []

    for siteCls in crawl_sites:
        allowed_domains.extend(siteCls.allow)
        start_urls += siteCls.start_urls
        rules_allow.append(siteCls.allow_re)
        rules_deny.append(siteCls.deny_re)

    rules = (
         Rule(LinkExtractor(allow=rules_allow), 
                            callback='parse_news',
                            follow=False),
         Rule(LinkExtractor(allow=('.*', ), deny=rules_deny), 
                            callback='log_skipped',
                            follow=True),
    )


    def __init__(self):
        super(TrNewsSpider, self).__init__()
        self.parser = set()
#        self.radikal = Radikal(logger=self.log)
        for cls in crawl_sites:
            self.parser.add((cls(logger=self.log), cls.allow_re))
            self.req_count = 0

    def parse_news(self, response):
        for p, r in self.parser:
            if re.search(r, response.url):
                p.extract(response)
                return

    def log_skipped(self, response):
        self.log("Skipping %s " % response.url, level=log.INFO)
#        pass
#        if not re.search(r'www.cumhuriyet.com.tr/(video|foto|zaman_tuneli)/', response.url):
