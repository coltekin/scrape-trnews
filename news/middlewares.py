# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.exceptions import CloseSpider
from scrapy.exceptions import IgnoreRequest
from scrapy.http import TextResponse
from scrapy import log
import sys, os, signal

class ExitOn400:
    """ The spider gets stuck while crawling Cumhuriyet at some point
    after receiving a 400 response.
    This exits the spider when that happens. Hopefully persisitent
    state allows the next run to pick up from where we are left.
    """
    def process_response(self, request, response, spider):
        if response.status == 400:
            try:
                spider.to_be_killed = True
                raise CloseSpider('HTTP response 400 received.')
            finally:
                sys.exit("Received 400")
        else:
            return response

class LogResponseCode:
    def process_response(self, request, response, spider):
        if request.url == 'http://www.milliyet.com.tr/':
            r = TextResponse(url = request.url, body = response.body, encoding = 'UTF-8')
            log.msg("Encodign for http://www.milliyet.com.tr/: %s" %
                    response.encoding, log.WARNING, spider=spider)
        if response.status == 400:
            log.msg("Received HTTP status %d for %s" %
                    (response.status, request.url), log.WARNING, spider=spider)
            log.msg("Method: %s\nHeaders: \n%s\nBody: \n%s\nCookies: \n%s\nEncoding: \n%s\n" %
                    (request.method, request.headers, request.body, request.cookies, request.encoding), 
                    log.WARNING, spider=spider)
#            pgid = os.getpgid(0)
#            os.kill(pgid, signal.CTRL_C_EVENT)
        return response

class SpiderClosing:
    def process_request(self, request, spider):
        if spider.to_be_killed:
            log.msg("Spider has been killed, ignoring request to %s" % request.url, log.DEBUG, spider=spider)
#            raise IgnoreRequest()
            return request
        else:
            return None
