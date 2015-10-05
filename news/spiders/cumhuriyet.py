# -*- coding: utf-8 -*-
import scrapy
import re

from scrapy.http import Request
import datetime

from bs4 import BeautifulSoup

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from news_spider import NewsSpider

from news.util import write_content, get_first_match, normalize_date

class CumhuriyetSpider(NewsSpider):
    name = "cumhuriyet"
    allowed_domains = ["www.cumhuriyet.com.tr"]
    start_urls = ('http://www.cumhuriyet.com.tr/',)

    allow_pattern = (r"www.cumhuriyet.com.tr/"
                      "(?P<cat>"
                      "koseyazisi|"
                      "haber/[^/]+)"
                      "/(?P<id>[0-9]+)/.+"
    )

    deny_pattern = r"www.cumhuriyet.com.tr/(arama|kaydet|zaman_tuneli|cizim|spor|.*foto.*|.*video.*|rss|uye|.*secim.*)/"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

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

        author = get_first_match(response, 
                ('//div[@id="author"]//div[@class="name"]/text()',)
            )

        if not author:
            author = ""
            if category == 'koseyazisi':
                self.log.warning("No author in: %s" % response.url)

        title = get_first_match(response, 
                ('//div[@id="article-title" and @itemprop="headline"]/text()',
                 '//div[@id="news-header"]/h1[@class="news-title"]/text()',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url) 

        source = get_first_match(response, 
                ('//div[@id="content"]//div[@class="publish-date"]/div[@class="left"]/span/text()',)
            )

        if not source:
            source = ""
            if category != 'koseyazisi':
                self.log.info("Cannot find source in: %s" % response.url)


        pubdate = get_first_match(response, 
                ('//div[@id="content"]//div[@class="publish-date"]/div[@class="right"]/span/text()',
                 '//div[@id="content"]//div[@id="publish-date"]/text()',)
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
                ('//div[@id="content"]//div[@id="news-header"]/div[@class="news-short"]/text()',)
            )

        if not summary:
            summary = ""
            self.log.warning("No summary in: %s" % response.url) 

        content = get_first_match(response, 
                ('//div[@id="content"]//div[@id="news-body" or @id="article-body"]',)
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
                    summary = summary,
                    category = category,
                    article_id = aId,
                    url = response.url,
                    downloaded = datetime.datetime.utcnow().isoformat(),
                    newspaper = self.__class__.name
                )

        if success:
            self.log.info("Scraped: url=`%s' file=`%s'" % (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" % (response.url, fpath))

