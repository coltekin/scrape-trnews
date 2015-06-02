# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')


class Radikal:
    allow = ["www.radikal.com.tr"]
    data_path = "radikal"
    start_urls = ('http://www.radikal.com.tr/',)

    allow_pattern = (r"www.radikal.com.tr/("
                   "astroloji|"
                   "cevre|"
                   "dunya|"
                   "ekonomi|"
                   "geek|"
                   "gusto|"
                   "hayat|"
                   "politika|"
                   "saglik|"
                   "sinema|"
                   "spor|"
                   "teknoloji|"
                   "turkiye|"
                   "yasam|"
                   "yazarlar|"
                   "yemek_tarifleri|"
                   "yenisoz|"
                   "[^/]*_haber)"
                   "/.+"
    )

    allow_re = re.compile(allow_pattern)

    def __init__(self, logger=None):
        self.log = logger
        self.page_scraped = 0

    def extract(self, response):
        self.log('Match: %s.' % response.url, level=log.INFO)
        try:
            aId = (response
                .xpath('//input[@name="ArticleID" and @type="hidden"]/@value')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            self.log('No article id for %s, skipping.' % response.url, 
                level=log.WARNING)
            return

        d = Radikal.data_path + "/" + aId[:2] + "/" + aId[2:4]
        if not os.path.isdir(d):
            os.makedirs(d)
        f = d + "/" + aId + ".gz"
        if os.path.exists(f):
            self.log('Article %s exists (%s), skipping.' % 
                (aId, response.url), level=log.INFO)
            return

        try:
            category = re.search(Radikal.allow_re, response.url).group(1)
        except:
            self.log('URL %s does not match.' % response.url, 
                level=log.WARNING)
            return

        self.page_scraped += 1
        self.log('Scraping %s[%d]' % (response.url, self.page_scraped), 
                level=log.INFO)
        try: 
            author = ( response
                .xpath('//article//a[@class="name" and @itemprop="author"]/h3')
                .extract()[0]
                .encode('utf-8')
                .replace('<h3>', '')
                .replace('</h3>', '')
                .split('<br>')
            )
        except:
            author = []

        try:
            editor = (response
                .xpath('//span[@id="editorName"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            editor = ''

        if not (author or editor):
            self.log("No author or editor in: %s" % response.url,
                    level=log.WARNING)

        try: 
            title = (response
                .xpath('//div[@class="text-header" and @itemprop="name"]/h1/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            try:
                title = (response
                    .xpath('//input[@id="hiddenTitle" and @type="hidden"]/@value')
                    .extract()[0]
                    .encode('utf-8')
                )
            except:
                title = ""
                self.log("Cannot find title in: %s" % response.url, 
                        level=log.WARNING)


        try:
            pubdate = ( response
                .xpath('//article//span[@class="date" and @itemprop="datePublished"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            pubdate = ''
            self.log("Cannot find pubdate in: %s" % response.url,
                    level=log.WARNING)


        try:
            summary = ( response
                .xpath('//article//h6[@itemprop="articleSection"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            try:
                summary = (response
                    .xpath('//input[@id="hiddenSpot" and @type="hidden"]/@value')
                    .extract()[0]
                    .encode('utf-8')
                )
            except:
                summary = ''
                self.log("Cannot find summary in: %s" % response.url,
                        level=log.WARNING)

        try:
            content = ( response
                .xpath('//article//div[@itemprop="articleBody"]')
                .extract()[0]
                .encode('utf-8')
                .replace('\r', '')
            )
        except:
            content = ''
            self.log("Cannot find content in: %s" % response.url,
                    level=log.WARNING)

        with gzip.open(f, "wb") as fp:
            fp.write('<article>\n  <author>\n')
            for i in author:
                fp.write('    <namepart>%s</namepart>\n' % i)
            fp.write('  </author>\n')
            fp.write('  <pubdate>%s</pubdate>\n' % pubdate)
            fp.write('  <editor>%s</editor>\n' % editor)
            fp.write('  <title>%s</title>\n' % title)
            fp.write('  <summary>\n%s\n  </summary>\n' % summary)
            fp.write('  <category>%s</category>\n' % category)
            fp.write('  <article_id>%s</article_id>\n' % aId)
            fp.write('  <newspaper>radikal</newspaper>\n')
            fp.write('  <url>%s</url>\n' % response.url)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
