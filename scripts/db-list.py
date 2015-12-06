#!/usr/bin/python

import shelve,sys

db = shelve.open(sys.argv[1], 'r')
for key in db:
    print(key)
db.close()
