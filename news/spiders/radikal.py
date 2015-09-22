# -*- coding: utf-8 -*-
import scrapy
import re
import anydbm

from scrapy.http import Request
import datetime

from bs4 import BeautifulSoup

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from news_spider import NewsSpider

from news.util import write_content, get_first_match, normalize_date

class RadikalSpider(NewsSpider):
    name = "radikal"
    allowed_domains = ["radikal.com.tr"]
    start_urls = (
        'http://www.radikal.com.tr/',
    )

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

    deny_pattern = r"/arama/"

    allow_re = re.compile(allow_pattern)
    deny_re = re.compile(deny_pattern)

    def extract(self, response):

        try:
            m = re.search(self.__class__.allow_re, response.url)
            aId = m.group('id')
            category = m.group('cat')
        except:
#            e = sys.exc_info()[0]
            self.log.warning('URL %s does not match.' % response.url)
            return

        aId = int(aId)

        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped))

        author_fname = get_first_match(response, 
                ('//article//a[@class="name" and @itemprop="author"]/h3/text()[1]',)
            )

        author_sname = get_first_match(response, 
                ('//article//a[@class="name" and @itemprop="author"]/h3/text()[2]',)
            )

        if not (author_fname or author_sname):
            author = ""
            if category == 'koseyazisi':
                self.log.warning("No author in: %s" % response.url)
        else:
            author = author_fname + " " + author_sname

        title = get_first_match(response, 
                ('//div[@class="text-header" and @itemprop="name"]/h1/text()',
                 '//input[@id="hiddenTitle" and @type="hidden"]/@value',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url)
            return

        pubdate = get_first_match(response, 
                ('//article//span[@class="date" and @itemprop="datePublished"]/text()',)
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate: # TODO: interpolate when not fund
                self.log.warning("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url))
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log.warning("No pubdate in: %s" % response.url)

        summary = get_first_match(response, 
                ('//article//h6[@itemprop="articleSection"]/text()',
                 '//input[@id="hiddenSpot" and @type="hidden"]/@value',)
            )

        if not summary:
            summary = ""
            self.log.debug("No summary in: %s" % response.url)

        content = get_first_match(response, 
                ('//article//div[@itemprop="articleBody"]',)
            )

        if not content:
            content = ''
            self.log.warning("No content in: %s" % response.url)
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
            self.log.info("Scraped: url=`%s' file=`%s'" % (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" % (response.url, fpath))
