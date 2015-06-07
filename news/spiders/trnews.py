# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')

from extractor.radikal import Radikal
from extractor.cumhuriyet import Cumhuriyet
from extractor.t24 import T24
from extractor.milliyet import Milliyet
from extractor.zaman import Zaman
from extractor.sabah import Sabah
from extractor.zaytung import Zaytung

crawl_sites = {Zaytung}
#crawl_sites = {Milliyet, Radikal, T24, Cumhuriyet, Zaman, Sabah, Zaytung}


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
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.parser = set()
#        self.radikal = Radikal(logger=self.log)
        for cls in crawl_sites:
            self.parser.add((cls(logger=self.log), cls.allow_re))
            self.req_count = 0

    def spider_closed(self, spider):
        for p, r in self.parser:
            p.close()

    def parse_news(self, response):
        for p, r in self.parser:
            if re.search(r, response.url):
                p.extract(response)
                return

    def log_skipped(self, response):
        self.log("Skipping %s " % response.url, level=log.INFO)
#        pass
