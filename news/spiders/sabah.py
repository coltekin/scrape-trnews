# -*- coding: utf-8 -*-
import scrapy
import re
import anydbm

from scrapy.http import Request
import datetime
import logging

from bs4 import BeautifulSoup

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from news_spider import NewsSpider

from news.util import write_content, get_first_match, normalize_date

class SabahSpider(NewsSpider):
    name = "sabah"
    allowed_domains = ["www.sabah.com.tr"]
    start_urls = ('http://www.sabah.com.tr/',)

    allow_pattern = (r"www.sabah.com.tr/"
                      "(?P<cat>[^/]+)/((?P<subcat>[^/]+)/)?"
                      "[0-9]{4}/[0-9]{2}/[0-9]{2}/[^/]+$"

    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/arama\?"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def extract(self, response):

        aId = get_first_match(response, 
                ('//input[@id="ArticleId"]/@value',
                 '//input[@id="articleId"]/@value',
                 '//input[@name="ArticleId"]/@value',)
        )

        if not aId: # try to force HtmlResponse
            response = scrapy.http.HtmlResponse(url=response.url,
                    body=response.body)

        aId = get_first_match(response, 
                ('//input[@id="ArticleId"]/@value',
                 '//input[@id="articleId"]/@value',
                 '//input[@name="ArticleId"]/@value',)
        )

        if not aId:
            self.log.warning('No article id in %s.' % response.url) 

        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped)) 

        m = re.search(self.__class__.allow_re, response.url)
        category = m.group('cat')


        author = get_first_match(response, 
                ('//div[@class="yazarList"]/ul/li/div/a/strong/text()',)
            )

        if not author:
            author = ""
            if category == 'yazarlar':
                self.log.warning("No author in: %s" % response.url)

        title = get_first_match(response, 
                ('//meta[@itemprop="name"]/@content',
                 '//meta[@itemprop="headline"]/@content',
                 '//div[@class="mail"]/strong[@class="tit"]/text()',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url) 
            return

        pubdate = get_first_match(response, 
                ('//meta[@itemprop="datePublished"]/@content',)
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate:
                self.log.warning("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url)) 
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log.warning("No pubdate in: %s" % response.url)

        updated = get_first_match(response, 
                ('//meta[@itemprop="dateModified"]/@content',)
            )

        if updated:
            ndate = normalize_date(pubdate)
            if not ndate:
                updated = ""
                self.log.debug("Cannot parse updated (%s) in: %s" % 
                        (pubdate, response.url))
        else:
            updated = ""


        content = get_first_match(response, 
                ('//article[@id="contextual"]',)
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
                    updated = updated,
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

