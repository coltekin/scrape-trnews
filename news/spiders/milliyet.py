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

class MilliyetSpider(NewsSpider):
    name = "milliyet"
    allowed_domains = ["www.milliyet.com.tr"]
    start_urls = ('http://www.milliyet.com.tr/',)
    allow_pattern = (r"www.milliyet.com.tr/[^/]+/"
                      "(?P<cat1>[^/]+)/"
                      "(?P<typ1>detay|ydetay)/"
                      "(?P<id1>[0-9]+)/"
                      "default.htm"
                      "|"
                      "www.milliyet.com.tr/.+(?P<typ2>-)"
                      "(?P<cat2>"
                      "magazin|"
                      "gundem|"
                      "sinema|"
                      "kitap|"
                      "teknoloji|bilim|internet|cevre|denedik|sektorel|uzay|bilisim|mobildunya|dijitalfotograf|dijitaloyuncaklar|"
                      "[^-]+-yerelhaber|"
                      "oyundunyasi|konut|otomobil|oyun|"
                      "universite|otoyazarlar|okuloncesiegitim|"
                      "lise|egitimyurtdisi|egitimsbs|egitimdunyasi|egitimdigersinavlar|"
                      "ygs|motorsporlari|ilkogretim|dapyapi|egitimoss|ticariarac|bakimpratik|"
                      "otoguncel|otokampanya|konsept|motosiklet|yenimodel|tatil|yeniurunler|"
                      "egitim)-"
                      "(?P<id2>[0-9]+)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "(?P<cat3>ege|ekonomi|cafe|guncel|cadde|cumartesi|pazar|tatil|gundem|spor|sinema|siyaset|yasam|magazin|dunya)/"
                      "(?P<typ3>(ekonomi|haber|yeniurunler|gundem|magazin|siyaset|magazin|dunya|spor)?(yazar)?detay(arsiv)?)/"
                      "[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9]/"
                      "(?P<id3>[0-9]+)/"
                      "default.htm"
                      "|"
                      "www.milliyet.com.tr/.+-"
                      "(?P<cat4>[^-]*)-"
                      "(?P<id4>[0-9]+)"
                      "-(?P<typ4>skorer-yazar-yazisi|skorerhaber)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "-pembenar-(?P<typ5>detay|yazardetay)"
                      "-(?P<cat5>[^-]+)"
                      "-(?P<id5>[0-9]+)/"
    )

    deny_pattern = (r"/arama|ArsivAramaSonuc|SkorerArama"
                     "|Milliyet-Tv|Skorer-Tv|/fotogaleri/"
                     "|-galeri-/"
                     "|dijitalfotograf"
                     "| "
                     "|\n"
                     "|\r"
                     "|/vefat/"
                     "|yereletkinlik"
                     "|skorergaleri/"
                )

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    date_in_url_re = re.compile(r"www.milliyet.com.tr/.+/"
                      "cadde|cumartesi|pazar|tatil/"
                      "haberdetayarsiv|gundemyazardetay|haberdetay|yazardetay/"
                      "(?P<date>[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9])/"
                      "[0-9]+/"
                      "default.htm"
        )

    def extract(self, response):

        try:
            m = re.search(self.__class__.allow_re, response.url)
            for i in list(range(1,6)):
                aId = m.group('id%d' % i)
                if aId:
                    category = m.group('cat%d' % i)
                    article_type = m.group('typ%d' % i)
                    break
        except:
            e = sys.exc_info()[0]
            self.log.warning('URL %s does not match.' % response.url + e) 
            return

        aId = int(aId)

        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped)) 

        author = get_first_match(response, 
                ('//div[@class="ynfo"]/a[@class="yadi"]/text()',
                 '//div[@class="yazarBox"]//strong[@itemprop="name"]/text()',
                 '//div[@class="authnfo"]/a[@class="yname"]/strong/text()',
                 '//div[@class="contentY"]/p[1]/strong/text()',
                 '//div[@class="writer"]//span[@class="wname"]/text()',
                 '//p[@class="imza"]/text()',)
            )

        if not author:
            author = ""
            if article_type == 'ydetay' or 'yazar' in article_type:
                self.log.warning("No author in: %s" % response.url)

        title = get_first_match(response, 
                ('//h1[@itemprop="name"]/text()',
                 '//div[@class="detayTop"]//h1/text()',
                 '//div[@class="dContent"]//h1[@class="trc"]/text()',
                 '//input[@id="hiddenTitle"]/@value',
                 '//div[@class="haber"]/div[@class="tcontent"]/h3/text()',)
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url)

        pubdate = get_first_match(response, 
                ('//meta[@itemprop="datePublished"]/@content',
                 '//div[@class="tTools"]//span/text()',
                 '//div[@class="detayTop"]//div[@class="date"]/text()',
                 '//div[@class="tools"]/div[@class="dt"]/text()',)
            )

        updated = get_first_match(response, 
                ('//meta[@itemprop="dateModified"]/@content')
            )

        if pubdate and "|" in pubdate:
            pub, upd = pubdate.split("|")
            pubdate = pub.strip()
            updated = upd.strip()
        else:
            if not updated:
                updated = ""

        if not pubdate:
            m = re.match(self.__class__.date_in_url_re, response.url)
            if m:
                pubdate = m.group('date')

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate: # TODO: interpolate when not fund
                self.log.warning("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url)) 
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log.warning("No pubdate in: %s" % response.url)

        subtitle = get_first_match(response, 
                ('//h1[@itemprop="name"]/following-sibling::h2/text()',
                 '//div[@class="detayTop"]//h2/text()',
                 '//h1[@class="trc"]/following-sibling::h2/text()',)
            )


        if article_type in {"detay", "haberdetay", "haberdetayarsiv", "skorerhaber"} or article_type.endswith('-yerelhaber'):
            summary = subtitle
            subtitle = ""
        else:
            summary = ""

        content = get_first_match(response, 
                ('//div[@id="divAdnetKeyword3"]',
                 '//div[@id="artbody" or @id="articleBody"]',
                 '//div[@class="tcontent"]/div[@class="text"]',
                 '//div[@class="detayMain"]//div[@class="content"]',)
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
                    subtitle = subtitle,
                    author = author,
                    pubdate = pubdate,
                    updated = updated,
                    downloaded = datetime.datetime.utcnow().isoformat(),
                    summary = summary,
                    category = category,
                    article_id = aId,
                    url = response.url,
                    newspaper = self.__class__.name
                )

        if success:
            self.log.info("Scraped: url=`%s' file=`%s'" % (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" % (response.url, fpath))

