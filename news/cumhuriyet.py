# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log
import datetime

import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')

from bs4 import BeautifulSoup

from news.util import write_content, get_first_match, normalize_date

class Cumhuriyet:

    name = "cumhuriyet"
    allow = ["www.cumhuriyet.com.tr"]
    data_path = "cumhuriyet"
    start_urls = ('http://www.cumhuriyet.com.tr/',)

    allow_pattern = (r"www.cumhuriyet.com.tr/"
                      "(?P<cat>"
                      "koseyazisi|"
                      "haber/[^/]+)"
                      "/(?P<id>[0-9]+)/.+"
    )

    deny_pattern = r"www.cumhuriyet.com.tr/(arama|kaydet|foto|zaman_tuneli|video)/"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)


    def __init__(self, logger=None):
        self.log = logger
        self.article_ids = set()
        if (os.path.exists(self.__class__.name + '.article_ids')):
            with open(self.__class__.name + '.article_ids', "r") as fp:
                for line in fp:
                    self.article_ids.add(int(line.strip()))
        self.page_scraped = 0

    def close(self):
        with open(self.__class__.name + '.article_ids', "w") as fp:
            for aid in self.article_ids:
                fp.write("%s\n" % aid)

    def extract(self, response):



        try:
            m = re.search(self.__class__.allow_re, response.url)
            aId = m.group('id')
            category = m.group('cat')
        except:
#            e = sys.exc_info()[0]
            self.log('URL %s does not match.' % response.url, 
                level=log.WARNING)
            return

        aId = int(aId)
        if (aId in self.article_ids):
            self.log('Article %s exists (%s), skipping.' % 
                (aId, response.url), level=log.INFO)
            return
        else:
            self.article_ids.add(aId)

        self.page_scraped += 1
        self.log('Scraping %s[%d]' % (response.url, self.page_scraped), 
                level=log.DEBUG)

        author = get_first_match(response, 
                ('//div[@id="author"]//div[@class="name"]/text()',)
            )

        if not author:
            author = ""
            if category == 'koseyazisi':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        title = get_first_match(response, 
                ('//div[@id="article-title" and @itemprop="headline"]/text()',
                 '//div[@id="news-header"]/h1[@class="news-title"]/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)

        source = get_first_match(response, 
                ('//div[@id="content"]//div[@class="publish-date"]/div[@class="left"]/span/text()',)
            )

        if not source:
            source = ""
            if category != 'koseyazisi':
                self.log("Cannot find source in: %s" %
                    response.url, level=log.INFO)


        pubdate = get_first_match(response, 
                ('//div[@id="content"]//div[@class="publish-date"]/div[@class="right"]/span/text()',
                 '//div[@id="content"]//div[@id="publish-date"]/text()',)
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate: # TODO: interpolate when not fund
                self.log("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url), 
                        level=log.WARNING)
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log("No pubdate in: %s" % response.url, 
                    level=log.WARNING)


        summary = get_first_match(response, 
                ('//div[@id="content"]//div[@id="news-header"]/div[@class="news-short"]/text()',)
            )

        if not summary:
            summary = ""
            self.log("No summary in: %s" % response.url, 
                    level=log.DEBUG)

        content = get_first_match(response, 
                ('//div[@id="content"]//div[@id="news-body" or @id="article-body"]',)
            )

        if not content:
            content = ''
            self.log("No content in: %s" % response.url,
                    level=log.WARNING)
            return

        soup = BeautifulSoup(content, features="xml")
        for s in soup('script'): s.decompose()
        content = (soup.prettify().encode('utf-8'))


        fpath, success = write_content(content,
                    title = title,
                    author = author,
                    pubdate = pubdate,
                    summary = summary,
                    category = category,
                    article_id = aId,
                    url = response.url,
                    downloaded = datetime.datetime.utcnow().isoformat(),
                    newspaper = self.__class__.name
                )

        if success:
            self.log("Scraped: url=`%s' file=`%s'" % (response.url, fpath),
                    level=log.INFO)
        else:
            self.log("Duplicate: url=`%s' file=`%s'" % (response.url, fpath),
                    level=log.INFO)

