#!/bin/bash

UPDATE=1

if [[ "$1" == "redo" ]]; then
    UPDATE=0
fi

n=0
for d1 in trnews-data/??;do 
    echo -n "${d1}... "
    for d2 in $d1/??;do
        for f in $d2/????????????????;do 
            if [[ "$UPDATE" -eq 1 && -r ${f}.txt.gz ]]; then
                continue
            fi
            timeout 60 bash -c "zcat $f \
                | grep -v '^<?xml ' \
                | html2text -utf8 -nometa -width 999999 -rcfile html2text.rc \
                | gzip -c \
                > ${f}.txt.gz \
                || rm -f ${f}.txt.gz 2>/dev/null" 
            if [ $? = 124 ]; then
                echo -e " Timout processing $f" >> to-text.log
                rm -f ${f}.txt.gz
            fi
            let n=n+1
        done
    done
    echo "$n documents"
done
