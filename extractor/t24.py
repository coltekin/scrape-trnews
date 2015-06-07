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

class T24:

    name = "t24"
    allow = ["t24.com.tr"]
    start_urls = ('http://t24.com.tr/',)

    allow_pattern = (r"//t24.com.tr/"
                      "(?P<cat>yazarlar|"
                      "haber|"
                      "k24/[^/]+)"
                      "/[^,]+,(?P<id>[0-9]+)"
    )

    deny_pattern = r"m.t24.com.tr|t24.com.tr/(arama|video|foto-haber)/"

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
                ('//div[@class="context"]//div[@itemprop="author" and @class="name"]//a/text()',
                 '//div[@class="meta"]//a[@itemprop="author"]/text()',
                 '//div[@id="book-container"]//p[@class="author"]/text()',)
            )

        if not author:
            author = ""
            if category == 'koseyazisi':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        title = get_first_match(response, 
                ('//div[@class="top-context"]//h1[@itemprop="headline"]/text()',
                 '//div[@class="title"]/h1[@itemprop="headline"]/text()',
                 '//div[@id="book-container"]//h1[@class="title"]/text()',)
                 
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)

        summary = get_first_match(response, 
                ('//div[@class="title"]/div[@class="excerpt"]/p/text()',)
            )

        if not summary:
            summary = ""
            self.log("No summary in: %s" % response.url, 
                    level=log.DEBUG)



        pubdate = get_first_match(response, 
                ('//div[@class="article-content"]//div[@itemprop="datePublished"]/text()',
                 '//div[@class="story-content"]//div[@class="story-date"]/text()[2]',
                 '//div[@id="book-container"]//div[@class="content row"]/text()',)
            )

        if not pubdate:
            dm = get_first_match(response,
                    ('//div[@class="meta"]//span[@class="date"]/text()[1]',)
                )
            if not dm: dm = ""
            y = get_first_match(response,
                    ('//div[@class="meta"]//span[@class="date"]/span/text()',)
                )
            if not y: y = ""
            tm = get_first_match(response,
                    ('//div[@class="meta"]//span[@class="date"]/text()[2]',)
                )
            if not tm: tm = ""

            if dm or y or tm:
                pubdate = dm + " " + y + " " + tm


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

        content = get_first_match(response, 
                ('//div[@itemprop="articleBody"]',
                 '//div[@id="book-container"]//div[@class="col-xs-12"]',)
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

