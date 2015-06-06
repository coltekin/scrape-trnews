# -*- coding: utf-8 -*-

from scrapy.utils.request import request_fingerprint
import os, sys
import xxhash
import yaml
import gzip
import re
reload(sys)
sys.setdefaultencoding('utf-8')


weekdays = (u'[pP]azartesi|[sS]alı|[çÇ]arş(\.|amba)?|[pP]er(\.|şembe)?|[cC]uma')
months = (u'Ocak|Şubat|Mart|Nisan|Mayıs|Haziran'
          '|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık')
date_res = (
    re.compile(ur'(?P<Y>\d{4})-(?P<M>\d{2})-(?P<D>\d{2})T'
               '(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})Z?'),
    re.compile(ur'(?P<D>0?[1-9]|[12][0-9]|3[01]) +'
               '(?P<M>' + months + '),? +'
               ' *(' + weekdays + ')? *'
               '(?P<Y>\d{4})'
               '( *[-,] *(?P<h>[0-2][0-9]):(?P<m>[0-6][0-9])(:(?P<s>[0-6][0-9]))?)?'),
    re.compile(ur'(?P<D>0?[1-9]|[12][0-9]|3[01])[./]'
               '(?P<M>0?[1-9]|1[0-2])[./]'
               '(?P<Y>\d{4})'
               '( *[-,] *(?P<h>[0-2][0-9]):(?P<m>[0-6][0-9])(:(?P<s>[0-6][0-9]))?)?'),
)

month_map = {u'Ocak': '01',
         u'Şubat': '02',
         u'Mart': '03',
         u'Nisan': '04',
         u'Mayıs': '05',
         u'Haziran': '06',
         u'Temmuz': '07',
         u'Ağustos': '08',
         u'Eylül': '09',
         u'Ekim': '10',
         u'Kasım': '11',
         u'Aralık': '12'}

def get_first_match(response, paths):
    """Return the first extracted xpath or None
    """
    result = None
    for p in paths:
        try:
            result = (response
                .xpath(p)
                .extract()[0]
                .strip()
            )
            if result:
                break
        except:
            pass
    return result

def normalize_date(date):
    for rr in date_res:
        m = re.search(rr, date)
        if m:
            year = m.group('Y')
            month = m.group('M')
            if month in month_map: month = month_map[month]
            day = m.group('D')
            hour = m.group('h')
            if hour: hour = 'T' + hour
            else: hour = ''
            minute = m.group('m')
            if minute: minute = ':' + minute
            else: minute = ''
            second = m.group('s')
            if not second:  second = ''
            else: second = ':' +  second
            return "%s-%s-%s%s%s%s" % (year, month, day, hour, minute, second)
    return None

def write_content(content, **kwargs):

    h64 = xxhash.xxh64(content).hexdigest()
    filepath = 'trnews-data/' + h64[:2] + '/' + h64[2:4] + '/' + h64

    d = os.path.dirname(filepath)
    if not os.path.isdir(d):
        os.makedirs(d)
    elif os.path.exists(filepath):
        return filepath, False

    with open(filepath + ".meta", "wb") as fp:
        fp.write(yaml.safe_dump(kwargs, 
            default_flow_style = False, 
            allow_unicode=True, indent=2, encoding="utf-8"))

    with gzip.open(filepath, "wb") as fp:
        fp.write(content)

    return filepath, True
