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



class Sabah:
    name = "sabah"
    allow = ["www.sabah.com.tr"]
    start_urls = ('http://www.sabah.com.tr/',)

    allow_pattern = (r"www.sabah.com.tr/"
                      "(?P<cat>[^/]+)/((?P<subcat>[^/]+)/)?"
                      "[0-9]{4}/[0-9]{2}/[0-9]{2}/[^/]+$"

    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/arama\?"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.article_ids = set()
        if (os.path.exists(self.__class__.name + '.article_ids')):
            with open(self.__class__.name + '.article_ids', "r") as fp:
                for line in fp:
                    self.article_ids.add(line.strip())
        self.page_scraped = 0

    def close(self):
        with open(self.__class__.name + '.article_ids', "w") as fp:
            for aid in self.article_ids:
                fp.write("%s\n" % aid)

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
            self.log('No article id in %s.' % 
                response.url, level=log.WARNING)
        elif (aId in self.article_ids):
            self.log('Article %s exists (%s), skipping.' % 
                (aId, response.url), level=log.INFO)
            return
        else:
            self.article_ids.add(aId)

        self.page_scraped += 1
        self.log('Scraping %s[%d]' % (response.url, self.page_scraped), 
                level=log.DEBUG)

        m = re.search(self.__class__.allow_re, response.url)
        category = m.group('cat')


        author = get_first_match(response, 
                ('//div[@class="yazarList"]/ul/li/div/a/strong/text()',)
            )

        if not author:
            author = ""
            if category == 'yazarlar':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        title = get_first_match(response, 
                ('//meta[@itemprop="name"]/@content',
                 '//meta[@itemprop="headline"]/@content',
                 '//div[@class="mail"]/strong[@class="tit"]/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)
            return

        pubdate = get_first_match(response, 
                ('//meta[@itemprop="datePublished"]/@content',)
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate:
                self.log("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url), 
                        level=log.WARNING)
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log("No pubdate in: %s" % response.url, 
                    level=log.WARNING)

        updated = get_first_match(response, 
                ('//meta[@itemprop="dateModified"]/@content',)
            )

        if updated:
            ndate = normalize_date(pubdate)
            if not ndate:
                updated = ""
                self.log("Cannot parse updated (%s) in: %s" % 
                        (pubdate, response.url), level=log.DEBUG)
        else:
            updated = ""


        content = get_first_match(response, 
                ('//article[@id="contextual"]',)
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
                    updated = updated,
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

