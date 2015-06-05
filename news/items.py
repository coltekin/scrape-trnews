# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TrNewsItem(scrapy.Item):
    author = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    author = scrapy.Field()
    pubdate = scrapy.Field()
    updated = scrapy.Field()
    editor = scrapy.Field()
    source = scrapy.Field()
    summary = scrapy.Field()
    category = scrapy.Field()
    article_id = scrapy.Field()
    url = scrapy.Field()
    newspaper = scrapy.Field()
