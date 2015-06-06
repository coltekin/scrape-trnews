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

class Zaman:
    name = "zaman"
    allow = ["www.zaman.com.tr"]
    start_urls = ('http://www.zaman.com.tr/',)

    allow_pattern = (r"www.zaman.com.tr/"
                      "(?P<cat1>[^/]+)/"
                      "[^/]*"
                      "_(?P<id1>[0-9]+)\.html"
                      "|www.zaman.com.tr/"
                      "(?P<cat2>[^_]+)_"
                      "[^_]*"
                      "_(?P<id2>[0-9]+)\.html"
    )
#                      "gundem|ekonomi|spor|egitim|dunya"
#                      "|aile-saglik|kultur|magazin|"

    deny_pattern = (r"/search.action|/panaroma_|/video"
                )

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
            for i in list(range(1,3)):
                aId = m.group('id%d' % i)
                if aId:
                    category = m.group('cat%d' % i)
                    break
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
                ('//div[@class="yazarWrap"]/div/h5[@itemprop="name"]/text()',
                 '//span[@class="detayMuhabir"]/span[@itemprop="author"]/text()',)
            )

        if not author:
            author = ""
            self.log("No author in: %s" % response.url,
                level=log.WARNING)

        title = get_first_match(response, 
                ('//div[@id="sonYazi"]/h1[@itemprop="name"]/text()',
                 '//h1[@itemprop="headline"]/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)

        summary = get_first_match(response, 
                ('//div[@class="imgCaption"]/span/text()',)
            )

        if not summary:
            summary = ""
            self.log("No summary in: %s" % response.url, 
                    level=log.DEBUG)



        pubdate = get_first_match(response, 
                ('//meta[@itemprop=dateCreated"]/@content',
                 '//div[@id="sonYazi"]//div[@class="detayTarih"]/text()',
                 '//div[@itemprop="dateCreated"]/text()[2]',)
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

        content = get_first_match(response, 
                ('//div[@id="sonYazi"]//span[@itemprop="articleBody"]',
                 '//div[@class="detayText"]//span[@itemprop="articleBody"]',)
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

