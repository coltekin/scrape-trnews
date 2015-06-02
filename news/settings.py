# -*- coding: utf-8 -*-

# Scrapy settings for news project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'news'

SPIDER_MODULES = ['news.spiders']
NEWSPIDER_MODULE = 'news.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'news (+http://www.yourdomain.com)'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0 Iceweasel/31.6.0'

DEPTH_LIMIT = 15
DOWNLOAD_DELAY = 0.5

LOG_LEVEL = 'DEBUG'
LOG_FILE = 'news-scrap.log'

# following are for breadth-first search
#
# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
# SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'


AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_MAX_DELAY = 120
#AUTOTHROTTLE_DEBUG = True

DOWNLOADER_MIDDLEWARES = {
#    'news.middlewares.SpiderClosing': 50,
#    'news.middlewares.ExitOn400': 875,
    'news.middlewares.LogResponseCode': 875,
}

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr;en',
}

#CLOSESPIDER_PAGECOUNT = 50000
#CLOSESPIDER_TIMEOUT = 72000


COOKIES_ENABLED = False

