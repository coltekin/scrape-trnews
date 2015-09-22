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

class ZaytungSpider(NewsSpider):
    name = "zaytung"
    allowed_domains = ["zaytung.com"]
    start_urls = ('http://zaytung.com/',)

    allow_pattern = (r"/zaytung.com/"
                      "(?P<cat>haber|blog)detay.asp\?"
                      "newsid=(?P<id>[0-9]+) *$"
    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/aramasounc"

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

        title = get_first_match(response, 
                ('//div[@id="manset"]/div[1]/h2/text()',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url) 

        content = get_first_match(response, 
                ('//div[@id="manset"]/div[2]',)
            )

        # TODO: no date on the page. Possible options
        #       - interpolate from item_id
        #       - fetch the image, and use the HTTP last modified header
        pubdate = ""

        if not content:
            content = ''
            self.log.warning("No content in: %s" % response.url)
            return

        soup = BeautifulSoup(content, features="xml")
        for s in soup('script'): s.decompose()

        # find and remove the last <p> (does not belong to the content)
        for c in soup.div.children: 
            pass

        while c.name != u'p':
            for c in soup.div.children: 
                pass
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
            self.log.info("Scraped: url=`%s' file=`%s'" % (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" % (response.url, fpath))

