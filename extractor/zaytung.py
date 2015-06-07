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



class Zaytung:
    name = "zaytung"
    allow = ["zaytung.com"]
    start_urls = ('http://zaytung.com/',)

    allow_pattern = (r"/zaytung.com/"
                      "(?P<cat>haber|blog)detay.asp\?"
                      "newsid=(?P<id>[0-9]+) *$"
    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/aramasounc"

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

        title = get_first_match(response, 
                ('//div[@id="manset"]/div[1]/h2/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)

        content = get_first_match(response, 
                ('//div[@id="manset"]/div[2]',)
            )

        # TODO: no date on the page. Possible options
        #       - interpolate from item_id
        #       - fetch the image, and use the HTTP last modified header
        pubdate = ""

        if not content:
            content = ''
            self.log("No content in: %s" % response.url,
                    level=log.WARNING)
            return

        soup = BeautifulSoup(content, features="xml")
        for s in soup('script'): s.decompose()

        # find and remove the last <p> (does not belong to the content)
        for c in soup.div.children: 
            pass

        self.log("Last child: %s" % c.name, level=log.INFO)
        while c.name != u'p':
            for c in soup.div.children: 
                pass
            self.log("not p: %s" % c.name, level=log.INFO)
            c.extract()
        c.decompose()

        content = (soup.prettify().encode('utf-8'))

        fpath, success = write_content(content,
                    title = title,
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

