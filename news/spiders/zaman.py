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

class ZamanSpider(NewsSpider):
    name = "zaman"
    allowed_domains = ["www.zaman.com.tr"]
    start_urls = ('http://www.zaman.com.tr/',)

    allow_pattern = (r"www.zaman.com.tr/"
                      "(?P<cat1>[^/]+)/"
                      "[^_]*"
                      "_(?P<id1>[0-9]+)\.html"
                      "|www.zaman.com.tr/"
                      "(?P<cat2>[^_]*)_"
                      "[^_]*"
                      "_(?P<id2>[0-9]+)\.html"
    )
#                      "gundem|ekonomi|spor|egitim|dunya"
#                      "|aile-saglik|kultur|magazin|"

    deny_pattern = (r"/search.action|/panaroma_|/video"
                )

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

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
            self.log.warning('URL %s does not match.' % response.url)
            return

        aId = int(aId)

        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped))

        author = get_first_match(response, 
                ('//div[@class="yazarWrap"]/div/h5[@itemprop="name"]/text()',
                 '//span[@class="detayMuhabir"]/span[@itemprop="author"]/text()',)
            )

        if not author:
            author = ""
            self.log.warning("No author in: %s" % response.url)

        title = get_first_match(response, 
                ('//div[@id="sonYazi"]/h1[@itemprop="name"]/text()',
                 '//h1[@itemprop="headline"]/text()',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url)

        summary = get_first_match(response, 
                ('//div[@class="imgCaption"]/span/text()',)
            )

        if not summary:
            summary = ""
            self.log.debug("No summary in: %s" % response.url)



        pubdate = get_first_match(response, 
                ('//meta[@itemprop=dateCreated"]/@content',
                 '//div[@id="sonYazi"]//div[@class="detayTarih"]/text()',
                 '//div[@itemprop="dateCreated"]/text()[2]',)
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate:
                self.log.warning("Cannot parse pubdate (%s) in: %s" %
                        (pubdate, response.url))
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log.warning("No pubdate in: %s" % response.url)

        content = get_first_match(response, 
                ('//div[@id="sonYazi"]//span[@itemprop="articleBody"]',
                 '//div[@class="detayText"]//span[@itemprop="articleBody"]',)
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
            self.log.info("Scraped: url=`%s' file=`%s'" %
                    (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" %
                    (response.url, fpath))

