# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')


class Milliyet:
    newspaper = "milliyet"
    allow = ["www.milliyet.com.tr"]
    data_path = "milliyet"
    start_urls = ('http://www.milliyet.com.tr/',)

    allow_pattern = (r"www.milliyet.com.tr/[^/]+/"
                      "(?P<cat1>[^/]+)/"
                      "(?P<typ1>detay|ydetay)/"
                      "(?P<id1>[0-9]+)/"
                      "default.htm"
                      "|"
                      "www.milliyet.com.tr/.+-"
                      "(?<cat2>"
                      "magazin|"
                      "gundem|"
                      "egitim)-"
                      "(?<id2>[0-9]+)/"
                      "|"
                      "www.milliyet.com.tr/.+"
                      "(?P<cat3>[^/]+)/"
                      "(?P<typ3>haberdetayarsiv|gundemyazardetay)/"
                      "[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9][0-9][0-9]/"
                      "(?P<id3>[0-9]+)/"
                      "default.htm"
    )

#
#                      "|www.milliyet.com.tr/.+"
#                      "-(P<category>magazin)"
#                      "-(P<id>[0-9]+)/"
#

    deny_pattern = (r"ArsivAramaSonuc|Milliyet-Tv|Skorer-Tv|/fotogaleri/"
                     "|galeri-[0-9]+/"
                     "|dijitalfotograf"
                )

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.page_scraped = 0

    def extract(self, response):
#        self.log('Match: %s.' % response.url, level=log.INFO)

        try:
            m = re.search(Milliyet.allow_re, response.url)
            aId = m.group('id1')
            if aId:
                category = m.group('cat1')
                article_type = m.group('typ1')
            elif aid = m.group('id2'):
                category = m.group('cat2')
                article_type = ""
            elif aid = m.group('id3'):
                category = m.group('cat3')
                article_type = m.group('typ3')
        except:
#            e = sys.exc_info()[0]
#            self.log(e, level=log.WARNING)
            self.log('URL %s does not match.' % response.url, 
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

        c_xpath = '//div[@id="divAdnetKeyword3"]'
        if category == 'cadde':
            a_xpath = '//div[@class="ynfo"]/a[@class="yadi"]/text()'
            t_xpath = '//h1[@itemprop="name"]/text()'
            t2_xpath = '//h1[@itemprop="name"]/following-sibling::h2/text()'
            d_xpath = '//div[@class="tTools"]//span/text()'
        else:
            a_xpath = '//div[@class="yazarBox"]//strong[@itemprop="name"]/text()'
            t_xpath = '//div[@class="detayTop"]//h1/text()'
            t2_xpath = '//div[@class="detayTop"]//h2/text()'
            d_xpath = '//div[@class="detayTop"]//div[@class="date"]/text()'

        try: 
            author = (response
                .xpath(a_xpath)
                .extract()[0]
                .encode('utf-8')
            )
        except:
            author = ""

        if not author:
            if article_type == 'ydetay':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)
        editor = ""

        try: 
            title = (response
                .xpath(t_xpath)
                .extract()[0]
                .encode('utf-8')
            )
        except:
            title = ""
            self.log("Cannot find title in: %s" % response.url, 
                    level=log.WARNING)

        source = ""

        updated = ""
        try: 
            pubdate = (response
                .xpath('//meta[@itemprop="datePublished"]/@content')
                .extract()[0]
                .encode('utf-8')
                .strip()
            )
            if pubdate:
                updated = (response
                    .xpath('//meta[@itemprop="dateModified"]/@content')
                    .extract()[0]
                    .encode('utf-8')
                    .strip()
                )
        except:
            try:
                pubdate = (response
                    .xpath(d_xpath)
                    .extract()[0]
                    .encode('utf-8')
                    .strip()
                )
                if "|" in pubdate:
                    pub, upd = pubdate.split("|")
                    pubdate = pub.strip()
                    updated = upd.strip()
            except:
                pubdate = ""
                self.log("Cannot find pubdate in: %s" % response.url, 
                        level=log.WARNING)

        try:
            subtitle = (response
                .xpath(t2_xpath)
                .extract()[0]
                .encode('utf-8')
            )
        except:
            subtitle = ''
            self.log("Cannot find subtitle in: %s" % response.url,
                    level=log.DEBUG)

        try:
            content = (response
                .xpath(c_xpath)
                .extract()[0]
                .encode('utf-8')
                .replace('\r', '')
            )
        except:
            content = ''
            self.log("Cannot find content in: %s" % response.url,
                    level=log.WARNING)

        summary = ""
        if article_type == "detay":
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
            fp.write('  <newspaper>%s</newspaper>\n' % newspaper)
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
