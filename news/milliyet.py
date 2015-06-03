# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')

from bs4 import BeautifulSoup

class Milliyet:
    name = "milliyet"
    allow = ["www.milliyet.com.tr"]
    data_path = "milliyet"
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
                      "-[^-]+-yerelhaber|"
                      "oyundunyasi|konut|yerelhaber|otomobil|"
                      "yereletkinlik|universite|otoyazarlar|okuloncesiegitim|"
                      "lise|egitimyurtdisi|egitimsbs|egitimdunyasi|egitimdigersinavlar|"
                      "ygs|motorsporlari|ilkogretim|dapyapi|egitimoss|ticariarac|bakimpratik|"
                      "otoguncel|otokampanya|konsept|motosiklet|yenimodel|tatil|"
                      "egitim)-"
                      "(?P<id2>[0-9]+)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "(?P<cat3>cadde|cumartesi|pazar|tatil)/"
                      "(?P<typ3>haberdetayarsiv|gundemyazardetay|haberdetay|yazardetay)/"
                      "[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9]/"
                      "(?P<id3>[0-9]+)/"
                      "default.htm"
                      "|"
                      "www.milliyet.com.tr/.+-"
                      "(?P<cat4>[^-]+)-"
                      "(?P<id4>[0-9]+)"
                      "-(?P<typ4>skorer-yazar-yazisi|skorerhaber)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "-pembenar-(?P<typ5>detay|yazardetay)"
                      "-(?P<cat5>[^-]+)"
                      "-(?P<id5>[0-9]+)/"
    )

#
#                      "|www.milliyet.com.tr/.+"
#                      "-(P<category>magazin)"
#                      "-(P<id>[0-9]+)/"
#

    deny_pattern = (r"/arama|ArsivAramaSonuc|SkorerArama"
                     "|Milliyet-Tv|Skorer-Tv|/fotogaleri/"
                     "|-galeri-/"
                     "|dijitalfotograf"
                     "| "
                     "|\n"
                     "|\r"
                     "|skorergaleri/"
                )

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.page_scraped = 0

    def get_first_match(self, response, paths):
        """Return the first extracted xpath or None
        """
        result = None
        for p in paths:
            try:
                result = (response
                    .xpath(p)
                    .extract()[0]
                    .encode('utf-8')
                )
                if result:
                    break
            except:
                pass
        return result

    def extract(self, response):
#        self.log('Match: %s.' % response.url, level=log.INFO)

        try:
            m = re.search(Milliyet.allow_re, response.url)
            layout = 1
            for i in list(range(1,6)):
                aId = m.group('id%d' % i)
                if aId:
                    category = m.group('cat%d' % i)
                    article_type = m.group('typ%d' % i)
                    layout = i
                    break
        except:
            e = sys.exc_info()[0]
#            self.log(e, level=log.WARNING)
            self.log('URL %s does not match.' % response.url + e, 
                level=log.WARNING)
            return

        tmpId = "%04d" % int(aId)
        d = Milliyet.data_path + "/" + tmpId[:2] + "/" + tmpId[2:4]
        if not os.path.isdir(d):
            os.makedirs(d)
        f = d + "/" + aId + ".gz"
        if os.path.exists(f):
            self.log('Article %s exists (%s), skipping.' % 
                (aId, response.url), level=log.INFO)
            return


        self.page_scraped += 1
        self.log('Scraping %s[%d]' % (response.url, self.page_scraped), 
                level=log.INFO)

        author = self.get_first_match(response, 
                ('//div[@class="ynfo"]/a[@class="yadi"]/text()',
                 '//div[@class="yazarBox"]//strong[@itemprop="name"]/text()',
                 '//div[@class="authnfo"]/a[@class="yname"]/strong/text()',
                 '//div[@class="contentY"]/p[1]/strong/text()',
                 '//div[@class="writer"]//span[@class="wname"]/text()',
                 '//p[@class="imza"]/text()',)
            )

        if not author and article_type in {'ydetay', 'gundemyazardetay', 'yazardetay', 'skorer-yazar-yazisi'}:
            author = ""
            self.log("No author in: %s" % response.url,
                level=log.WARNING)
        editor = ""


        title = self.get_first_match(response, 
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

        source = ""

        pubdate = self.get_first_match(response, 
                ('//meta[@itemprop="datePublished"]/@content',
                 '//div[@class="tTools"]//span/text()',
                 '//div[@class="detayTop"]//div[@class="date"]/text()',
                 '//div[@class="tools"]/div[@class="dt"]/text()',)
            )

        updated = self.get_first_match(response, 
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
            pubdate = ""
            self.log("No pubdate in: %s" % response.url, 
                    level=log.WARNING)


        subtitle = self.get_first_match(response, 
                ('//h1[@itemprop="name"]/following-sibling::h2/text()',
                 '//div[@class="detayTop"]//h2/text()',
                 '//h1[@class="trc"]/following-sibling::h2/text()',)
            )

        content = self.get_first_match(response, 
                ('//div[@id="divAdnetKeyword3"]',
                 '//div[@id="artbody" or @id="articleBody"]')
            )

        if not content:
            content = ''
            self.log("No content in: %s" % response.url,
                    level=log.WARNING)

        soup = BeautifulSoup(content, features="xml")
        for s in soup('script'): s.decompose()
        content = (soup.prettify()
                      .replace('<?xml version="1.0" encoding="utf-8"?>\n', '')
                      .encode('utf-8')
                  )

        summary = ""
        if article_type in {"detay", "haberdetay", "haberdetayarsiv", "skorerhaber"}:
            summary = subtitle
            subtitle = ""

        with gzip.open(f, "wb") as fp:
            fp.write('<article>\n')
            fp.write('<author>%s</author>\n' % author)
            fp.write('  <pubdate>%s</pubdate>\n' % pubdate)
            fp.write('  <updated>%s</updated>\n' % updated)
            fp.write('  <editor>%s</editor>\n' % editor)
            fp.write('  <title>%s</title>\n' % title)
            fp.write('  <subtitle>%s</subtitle>\n' % title)
            fp.write('  <source>%s</source>\n' % source)
            fp.write('  <summary>\n%s\n  </summary>\n' % summary)
            fp.write('  <category>%s</category>\n' % category)
            fp.write('  <article_id>%s</article_id>\n' % aId)
            fp.write('  <newspaper>%s</newspaper>\n' % Milliyet.name)
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
