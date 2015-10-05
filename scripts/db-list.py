#!/usr/bin/python

import dbm,sys

print(sys.argv[1])

db = dbm.open(sys.argv[1], 'r')
for key in db.keys():
    print(key)
db.close()
