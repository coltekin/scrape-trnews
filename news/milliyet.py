# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')

from bs4 import BeautifulSoup

from news.util import write_content, get_first_match, normalize_date

class Milliyet:
    name = "milliyet"
    allow = ["www.milliyet.com.tr"]
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
                      "teknoloji|bilim|internet|cevre|denedik|sektorel|uzay|bilisim|mobildunya|dijitalfotograf|"
                      "[^-]+-yerelhaber|"
                      "oyundunyasi|konut|otomobil|"
                      "universite|otoyazarlar|okuloncesiegitim|"
                      "lise|egitimyurtdisi|egitimsbs|egitimdunyasi|egitimdigersinavlar|"
                      "ygs|motorsporlari|ilkogretim|dapyapi|egitimoss|ticariarac|bakimpratik|"
                      "otoguncel|otokampanya|konsept|motosiklet|yenimodel|tatil|"
                      "egitim)-"
                      "(?P<id2>[0-9]+)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "(?P<cat3>cafe|guncel|cadde|cumartesi|pazar|tatil|gundem|spor|sinema|siyaset|yasam|magazin|dunya)/"
                      "(?P<typ3>(haber|gundem|magazin|siyaset|magazin|dunya|spor)?(yazar)?detay(arsiv)?)/"
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
#        self.log('Match: %s.' % response.url, level=log.INFO)

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
#            self.log(e, level=log.WARNING)
            self.log('URL %s does not match.' % response.url + e, 
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
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        title = get_first_match(response, 
                ('//h1[@itemprop="name"]/text()',
                 '//div[@class="detayTop"]//h1/text()',
                 '//div[@class="dContent"]//h1[@class="trc"]/text()',
                 '//input[@id="hiddenTitle"]/@value',
                 '//div[@class="haber"]/div[@class="tcontent"]/h3/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)
            return

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
                self.log("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url), 
                        level=log.WARNING)
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log("No pubdate in: %s" % response.url, 
                    level=log.WARNING)


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
            self.log("No content in: %s" % response.url,
                    level=log.WARNING)
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
                    summary = summary,
                    category = category,
                    article_id = aId,
                    url = response.url,
                    newspaper = self.__class__.name
                )

        if success:
            self.log("Scraped: url=`%s' file=`%s'" % (response.url, fpath),
                    level=log.INFO)
        else:
            self.log("Duplicate: url=`%s' file=`%s'" % (response.url, fpath),
                    level=log.INFO)

