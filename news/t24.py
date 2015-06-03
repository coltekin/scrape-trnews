# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')


class T24:
    name = "t24"
    allow = ["t24.com.tr"]
    data_path = "t24"
    start_urls = ('http://t24.com.tr/',)

    allow_pattern = (r"t24.com.tr/("
                      "yazarlar|"
                      "haber|"
                      "k24/[^/]+)"
                      "/[^,]+,([0-9]+)"
    )

    deny_pattern = r"m\.t24\.com\.tr|t24.com.tr/(arama|video|foto-haber)/"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.page_scraped = 0

    def extract(self, response):
#        self.log('Match: %s.' % response.url, level=log.INFO)

        try:
            m = re.search(T24.allow_re, response.url)
            aId = m.group(2)
            category = m.group(1)
        except:
#            e = sys.exc_info()[0]
#            self.log(e, level=log.WARNING)
            self.log('URL %s does not match.' % response.url, 
                level=log.WARNING)
            return

        tmpId = "%04d" % int(aId)
        d = T24.data_path + "/" + tmpId[:2] + "/" + tmpId[2:4]
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
                .xpath('//div[@class="context"]//div[@itemprop="author" and @class="name"]//a/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            author = ""

        if not author:
            if category == 'yazarlar':
                self.log("No author in: %s" % response.url,
                    level=log.WARNING)

        editor = ""

        try: 
            title = (response
                .xpath('//div[@class="top-context"]//h1[@itemprop="headline"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            title = ""
            self.log("Cannot find title in: %s" % response.url, 
                    level=log.WARNING)

        source = ""

        try: 
            pubdate = (response
                .xpath('//div[@class="article-content"]//div[@itemprop="datePublished"]/text()')
                .extract()[0]
                .encode('utf-8')
                .strip()
            )
        except:
            try:
                pubdate = (response
                    .xpath('//div[@class="story-content"]//div[@class="story-date"]/text()')
                    .extract()[1]
                    .encode('utf-8')
                    .strip()
                )
                if not re.search(r'[0-9]', pubdate):
                    self.log("Invalid pubdate '%s' find pubdate in: %s" % 
                            (pubdate, response.url), level=log.WARNING)
            except:
                pubdate = ""
                self.log("Cannot find pubdate in: %s" % response.url, 
                        level=log.WARNING)

        try:
            subtitle = (response
                .xpath('//div[@class="top-context"]//h2/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            subtitle = ''
            self.log("Cannot find subtitle in: %s" % response.url,
                    level=log.DEBUG)

        try:
            content = (response
                .xpath('//div[@itemprop="articleBody"]')
                .extract()[0]
                .encode('utf-8')
                .replace('\r', '')
            )
        except:
            content = ''
            self.log("Cannot find content in: %s" % response.url,
                    level=log.WARNING)

        summary = ""

        with gzip.open(f, "wb") as fp:
            fp.write('<article>\n')
            fp.write('<author>%s</author>\n' % author)
            fp.write('  <pubdate>%s</pubdate>\n' % pubdate)
            fp.write('  <editor>%s</editor>\n' % editor)
            fp.write('  <title>%s</title>\n' % title)
            fp.write('  <subtitle>%s</subtitle>\n' % title)
            fp.write('  <source>%s</source>\n' % source)
            fp.write('  <summary>\n%s\n  </summary>\n' % summary)
            fp.write('  <category>%s</category>\n' % category)
            fp.write('  <article_id>%s</article_id>\n' % aId)
            fp.write('  <newspaper>%s</newspaper>\n' % T24.name)
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
