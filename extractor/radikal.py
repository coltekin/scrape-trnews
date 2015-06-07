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



class Radikal:
    name = "radikal"
    allow = ["www.radikal.com.tr"]
    start_urls = ('http://www.radikal.com.tr/',)

    allow_pattern = (r"www.radikal.com.tr/"
                  "(?P<cat>"
                   "astroloji|"
                   "cevre|"
                   "dunya|"
                   "ekonomi|"
                   "geek|"
                   "gusto|"
                   "hayat|"
                   "politika|"
                   "saglik|"
                   "sinema|"
                   "spor|"
                   "teknoloji|"
                   "turkiye|"
                   "yasam|"
                   "yazarlar|"
                   "yemek_tarifleri|"
                   "yenisoz|"
                   "[^/]*_haber)"
                   "/.+-"
                   "(?P<id>[0-9]+) *$"
    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/arama/"

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

        author_fname = get_first_match(response, 
                ('//article//a[@class="name" and @itemprop="author"]/h3/text()[1]',)
            )

        author_sname = get_first_match(response, 
                ('//article//a[@class="name" and @itemprop="author"]/h3/text()[2]',)
            )

        if not (author_fname or author_sname):
            author = ""
            if category == 'koseyazisi':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)
        else:
            author = author_fname + " " + author_sname

        title = get_first_match(response, 
                ('//div[@class="text-header" and @itemprop="name"]/h1/text()',
                 '//input[@id="hiddenTitle" and @type="hidden"]/@value',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)
            return

        pubdate = get_first_match(response, 
                ('//article//span[@class="date" and @itemprop="datePublished"]/text()',)
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
                ('//article//h6[@itemprop="articleSection"]/text()',
                 '//input[@id="hiddenSpot" and @type="hidden"]/@value',)
            )

        if not summary:
            summary = ""
            self.log("No summary in: %s" % response.url, 
                    level=log.DEBUG)

        content = get_first_match(response, 
                ('//article//div[@itemprop="articleBody"]',)
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
                    category = category,
                    summary = summary,
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

