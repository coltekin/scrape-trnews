# -*- coding: utf-8 -*-
import scrapy
import re
import dbm

from scrapy.http import Request
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

import logging
import datetime

from bs4 import BeautifulSoup

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')


from news.util import write_content, get_first_match, normalize_date

class NewsSpider(scrapy.Spider):
    name = None
    allowed_domains = None
    start_urls = None

    allow_pattern = None
    deny_pattern = None

    allow_re = None
    deny_re = None

    def __init__(self, category=None, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(self.__class__.name)

        self.visited = dbm.open(self.__class__.name + '-visited', 'c')
        self.page_scraped = 0
        dispatcher.connect(self.close_spider, signals.spider_closed)

    def close_spider(self, spider):
        self.log.info("Closing the database...")
        self.visited.close()

    def parse(self, response):

        self.log.info('processing %s' % response.url)
        if re.search(self.__class__.allow_re, response.url):
            self.log.info('Extracting %s' % response.url)
            self.extract(response)
            self.visited[response.url.encode('utf8')] = "x"

        links = set(response.xpath("//a/@href"))
        for href in links:
            url = response.urljoin(href.extract()).encode('utf8')
            if self.__class__.deny_re and re.search(self.__class__.deny_re, url):
                self.log.debug('deny: %s' % url)
                continue
            if url in self.visited.keys():
                self.log.debug('visited: %s' % url)
                continue
            self.log.debug('yielding: %s (from %s)' % (url, response.url))
            yield(Request(url))
