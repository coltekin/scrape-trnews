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

class DWTrSpider(NewsSpider):
    name = "dw_tr"
    allowed_domains = ["www.dw.com"]
    start_urls = ('http://www.dw.com/tr/',)

    allow_pattern = (r"www.dw.com/tr/"
                      "(?P<title>[^/]+)"
                      "/a-(?P<id>[0-9]+)"
    )

    deny_pattern = (r"www.dw.com/(?!tr/)|"
            "www.dw.com/tr/(multimedya|yayinlarimiz|almanca-..renin)/")

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def extract(self, response):

        try:
            m = re.search(self.__class__.allow_re, response.url)
            aId = m.group('id')
            title_x = m.group('title')
        except:
#            e = sys.exc_info()[0]
            self.log.warning('URL %s does not match.' % response.url)
            return

        aId = int(aId)
        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped)) 

        title = get_first_match(response, 
               ('//head/meta[@property="og:title"]/@content',)
            )
# '//div[@id="bodyContent"]//div[@class="col3"]/h1/text()',
        title, _, category, pubdate = title.split("|")
    
        summary = get_first_match(response, 
            ('//div[@id="bodyContent"]//div[@class="col3"]/p[@class="intro"]/text()',)
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

        content = get_first_match(response, 
                ('//div[@id="bodyContent"]/div[@class="col3"]/div[@class="group"]/div[@class="longText"]',)
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
                    pubdate = pubdate,
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

