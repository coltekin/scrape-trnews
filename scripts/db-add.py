#!/usr/bin/python
from __future__ import print_function
import re, sys
import dbm

reload(sys)
sys.setdefaultencoding('utf-8')


sites =  {'sabah', 'radikal', 'milliyet', 't24.com.tr', 'cumhuriyet',
        'zaman', 'zaytung'}

dbs = dict()
scraped_re = re.compile(r".*Scraped: .*(?P<url>http://(?P<site>[^/]*)/[^']*)' .*")

for s in sites:
    dbs[s] = dbm.open(s + '-visited', 'c')

for line in sys.stdin:
    m = re.match(scraped_re, line)
    if m is not None:
        site = None
        for s in sites:
            if s in m.group('site'):
                site = s
                break
        dbs[site][m.group('url')] = "x"
#        print("{}: {}".format(site, m.group('url')))
            

for s in sites:
    dbs[s].close()
