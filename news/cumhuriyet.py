# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')


class Cumhuriyet:
    allow = ["www.cumhuriyet.com.tr"]
    data_path = "cumhuriyet"
    start_urls = ('http://www.cumhuriyet.com.tr/',)

    allow_pattern = (r"www.cumhuriyet.com.tr/("
                      "koseyazisi|"
                      "haber/[^/]+)"
                      "/([0-9]+)/.+"
    )

    deny_pattern = r"www.cumhuriyet.com.tr/(arama|kaydet|foto|zaman_tuneli|video)/"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.page_scraped = 0

    def extract(self, response):
#        self.log('Match: %s.' % response.url, level=log.INFO)

        try:
            m = re.search(Cumhuriyet.allow_re, response.url)
            aId = m.group(2)
            category = m.group(1)
        except:
#            e = sys.exc_info()[0]
#            self.log(e, level=log.WARNING)
            self.log('URL %s does not match.' % response.url, 
                level=log.WARNING)
            return

        tmpId = "%04d" % int(aId)
        d = Cumhuriyet.data_path + "/" + tmpId[:2] + "/" + tmpId[2:4]
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
        try: 
            author = (response
                .xpath('//div[@id="author"]//div[@class="name"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            author = ""

        if not author:
            if category == 'koseyazisi':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        editor = ""

        try: 
            title = (response
                .xpath('//div[@id="article-title" and @itemprop="headline"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            try:
                title = (response
                    .xpath('//div[@id="news-header"]/h1[@class="news-title"]/text()')
                    .extract()[0]
                    .encode('utf-8')
                )
            except:
                title = ""
                self.log("Cannot find title in: %s" % response.url, 
                        level=log.WARNING)

        try:
            source = (response
                .xpath('//div[@id="content"]//div[@class="publish-date"]/div[@class="left"]/span/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            source = ''
            if category != 'koseyazisi':
                self.log("Cannot find source in: %s" % response.url,
                    level=log.INFO)

        try:
            if source:
                xpath = '//div[@id="content"]//div[@class="publish-date"]/div[@class="right"]/span/text()'
            else:
                xpath = '//div[@id="content"]//div[@id="publish-date"]/text()'
            pubdate = (response
                .xpath(xpath)
                .extract()[0]
                .encode('utf-8')
            )
        except:
            pubdate = ''
            self.log("Cannot find pubdate in: %s" % response.url,
                    level=log.WARNING)

        try:
            summary = (response
                .xpath('//div[@id="content"]//div[@id="news-header"]/div[@class="news-short"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            summary = ''
            self.log("Cannot find summary in: %s" % response.url,
                    level=log.WARNING)

        try:
            content = (response
                .xpath('//div[@id="content"]//div[@id="news-body" or @id="article-body"]')
                .extract()[0]
                .encode('utf-8')
                .replace('\r', '')
            )
        except:
            content = ''
            self.log("Cannot find content in: %s" % response.url,
                    level=log.WARNING)

        with gzip.open(f, "wb") as fp:
            fp.write('<article>\n')
            fp.write('<author>%s</author>\n' % author)
            fp.write('  <pubdate>%s</pubdate>\n' % pubdate)
            fp.write('  <editor>%s</editor>\n' % editor)
            fp.write('  <title>%s</title>\n' % title)
            fp.write('  <source>%s</source>\n' % source)
            fp.write('  <summary>\n%s\n  </summary>\n' % summary)
            fp.write('  <category>%s</category>\n' % category)
            fp.write('  <article_id>%s</article_id>\n' % aId)
            fp.write('  <newspaper>radikal</newspaper>\n')
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
