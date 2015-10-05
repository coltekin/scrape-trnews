# -*- coding: utf-8 -*-
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

import scrapy
import re

from scrapy.http import Request,FormRequest
import datetime

from bs4 import BeautifulSoup


from news_spider import NewsSpider

from news.util import write_content, get_first_match, normalize_date

class SozcuSpider(NewsSpider):
    name = "sozcu"
    allowed_domains = ["www.sozcu.com.tr"]
#    start_urls = ('http://www.sozcu.com.tr/',)
    start_urls = ('http://www.sozcu.com.tr/',)

    allow_pattern = (r"/www.sozcu.com.tr/"
                      "(?P<cat>[^/]*)/"
                      ".*(?P<id>[0-9]+)/$"
    )

    allow_re = re.compile(allow_pattern)

    deny_pattern = r"/aramasounc"

    deny_re = re.compile(deny_pattern)
    allow_re = re.compile(allow_pattern)

    def extract(self, response):

        try:
            m = re.search(self.__class__.allow_re, response.url)
            aId = m.group('id')
            category = m.group('cat')
        except:
#            e = sys.exc_info()[0]
            self.log.warning('URL %s does not match.' % response.url) 
            return

        aId = int(aId)

        self.page_scraped += 1
        self.log.debug('Scraping %s[%d]' % (response.url, self.page_scraped))

        title = get_first_match(response, 
                ('//h1[@class="basdet"]/a[1]/text()',
                 '//h1[@itemprop="headline"]/text()',
                )
            )

        if not title:
            title = ""
            self.log.warning("No title in: %s" % response.url) 

        content = get_first_match(response, 
                ('//div[@itemprop="articleBody"]',
                 '//div[@class="content"]',
                )
            )

        if not content:
            content = ''
            self.log.warning("No content in: %s" % response.url)
            return

        soup = BeautifulSoup(content)
        if soup.body:
            soup = soup.body.next
        elif soup4.html:
            soup = soup.html.next

        for s in soup('script'): s.decompose()
        for s in soup('style'): s.decompose()
        for s in soup('img'): s.decompose()
        for s in soup('iframe'): s.decompose()
        for s in soup.findAll("div", {"id": "sozcu-detay-sosyal-paylasim"}):
            s.decompose()
        for s in soup.findAll("a", {"class": "post-banner-link"}):
            s.decompose()

        content = (soup.prettify().encode('utf-8'))


        author = get_first_match(response, 
                ('//div[@class="yazdet"/text()',
                )
            )


        if not author:
            author = ""
            if category == 'koseyazisi':
                self.log.warning("No author in: %s" % response.url)

        pubdate = get_first_match(response, 
                ( '//meta[@itemprop="datePublished"]/@content',
                  '//div[@class="tarihdet"]/p[1]/text()',
                )
            )

        if pubdate:
            ndate = normalize_date(pubdate)
            if not ndate: # TODO: interpolate when not fund
                self.log.warning("Cannot parse pubdate (%s) in: %s" % (pubdate, response.url))
            else:
                pubdate = ndate
        else:
            pubdate = ""
            self.log.warning("No pubdate in: %s" % response.url)


        summary = ""
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
            self.log.info("Scraped: url=`%s' file=`%s'" % (response.url, fpath))
        else:
            self.log.info("Duplicate: url=`%s' file=`%s'" % (response.url, fpath))


    def extract_extra_links(self, response):

        ret = list() 
        if response.url.encode('utf8').endswith('/'):
            form = response.xpath('//select[@id="Yil"]/..').extract_first()
            if form is not None:
                self.log.debug("Found form in %s" % response.url.encode('utf8'))
                for a in response.xpath('//select[@id="ay"]/option/@value'):
                    for y in response.xpath('//select[@id="Yil"]/option/@value'):
                        ay = a.extract().encode('utf8')
                        yil = y.extract().encode('utf8')
                        self.log.debug("adding %s:%s" % (yil, ay))
                        ret.append(FormRequest.from_response(response=response,
                            formxpath='//select[@id="Yil"]/..'.encode('utf8'),
                            formdata = {'ay': ay,
                                        'Yil': yil,
                                       },
                            clickdata = {'id': 'Yazi'}
                            ))
        return ret
