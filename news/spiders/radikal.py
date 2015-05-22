# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy import log

from news.items import NewsItem

import gzip
import sys, os, re
reload(sys)
sys.setdefaultencoding('utf-8')



class RadikalSpider(CrawlSpider):
    column_scraped = 0
    name = "radikal"
    data_path = "radikal"
    allowed_domains = ["radikal.com.tr"]
    start_urls = (
        'http://www.radikal.com.tr/yazarlar',
        'http://www.radikal.com.tr/',
    )
    url_pattern = (r"www.radikal.com.tr/("
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
                   "teknoloji|"
                   "turkiye|"
                   "yasam|"
                   "yazarlar|"
                   "yemek_tarifleri|"
                   "yenisoz|"
                   "[^/]*_haber)"
                   "/.+/.+"
    )
    url_re = re.compile(url_pattern)
    rules = (
         Rule(LinkExtractor(allow=(url_pattern)), 
                            callback='parse_radikal_article',
                            follow=True),
         Rule(LinkExtractor(allow=('.*', )), follow=True),
    )

    def parse_radikal_article(self, response):
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

        d = self.data_path + "/" + aId[:2] + "/" + aId[2:4]
        if not os.path.isdir(d):
            os.makedirs(d)
        f = d + "/" + aId + ".gz"
        if os.path.exists(f):
            self.log('Article %s exists (%s), skipping.' % 
                (aId, response.url), level=log.WARNING)
            return

        try:
            category = re.search(self.url_re, response.url).group(1)
        except:
            self.log('URL %s does not match.' % response.url, 
                level=log.WARNING)
            return

        self.column_scraped += 1
        self.log('Scraping %s[%d]' % (response.url, self.column_scraped), 
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
            author = ['Unknown']
            self.log("Cannot find auhor in: %s" % response.url, 
                    level=log.WARNING)

        try: 
            title = (response
                .xpath('//div[@class="text-header" and @itemprop="name"]/h1/text()')
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
            editor = (response
                .xpath('//span[@id="editorName"]/text()')
                .extract()[0]
                .encode('utf-8')
            )
        except:
            editor = ''
            self.log("No editor in: %s" % response.url,
                    level=log.WARNING)

        try:
            summary = ( response
                .xpath('//article//h6[@itemprop="articleSection"]/text()')
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
            fp.write('  <newspaper>%s</newspaper>\n' % self.name)
            fp.write('  <content>\n%s\n  </content>\n' % content)
            fp.write('</article>\n')
