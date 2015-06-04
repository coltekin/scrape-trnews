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

class Zaman:
    name = "zaman"
    allow = ["www.zaman.com.tr"]
    data_path = "zaman"
    start_urls = ('http://www.zaman.com.tr/',)

    allow_pattern = (r"www.zaman.com.tr/"
                      "(?P<cat1>[^/]+)/"
                      "[^/]*"
                      "_(?P<id1>[0-9]+)\.html"
                      "|www.zaman.com.tr/"
                      "(?P<cat1>[^_]+)_"
                      "[^_]*"
                      "_(?P<id1>[0-9]+)\.html"
    )
#                      "gundem|ekonomi|spor|egitim|dunya"
#                      "|aile-saglik|kultur|magazin|"

    deny_pattern = (r"/search.action|/panaroma_|/video"
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
            m = re.search(Zaman.allow_re, response.url)

            for i in list(range(1,3)):
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
        d = Zaman.data_path + "/" + tmpId[:2] + "/" + tmpId[2:4]
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
                ('//div[@class="yazarWrap"]/div/h5[@itemprop="name"]/text()',
                 )
            )

        if not author:
            author = ""
            self.log("No author in: %s" % response.url,
                level=log.WARNING)

        editor = self.get_first_match(response
                ('//div[@class="detayMuhabir"]/span/text()',)
            )


        title = self.get_first_match(response, 
                ('//div[@id="sonYazi"]/h1[@itemprop="name"]/text()',
                 '//h1[@itemprop="headline"]/text()',)
            )

        if not title:
            title = ""
            self.log("No title in: %s" % response.url, 
                    level=log.WARNING)

        source = ""

        pubdate = self.get_first_match(response, 
                ('//meta[@itemprop=dateCreated"]/@content'
                 '//div[@id="sonYazi"]//div[@class="detayTarih"]/text()',
                 '//div[@itemprop="dateCreated"]/text()[2]',)
            )

        updated = ""

        if not pubdate:
            pubdate = ""
            self.log("No pubdate in: %s" % response.url, 
                    level=log.WARNING)

        subtitle = ""

        content = self.get_first_match(response, 
                ('//div[@id="sonYazi"]//span[@itemprop="articleBody"]',)
                 '//div[@id="detayText"]//span[@itemprop="articleBody"]',)
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

        summary = self.get_first_match(response
                ('//div[@class="imgCaption"]/span/text()',)
            )

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
            fp.write('  <newspaper>%s</newspaper>\n' % Zaman.name)
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
