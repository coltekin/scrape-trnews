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

DEPTH_LIMIT = 5
DOWNLOAD_DELAY = 2

LOG_LEVEL = 'INFO'
LOG_FILE = 'news-scrap.log'
