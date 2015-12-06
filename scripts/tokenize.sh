#!/bin/bash

for d1 in trnews-data/??;do 
    echo $d1
    for d2 in $d1/??;do
        for f in $d2/????????????????.txt.gz;do 
            tf=$(echo $f|sed 's/\.gz/-tokenized.gz/')
            test -r $tf && continue
            echo $f
            timeout 30 bash -c "zcat $f \
                | sed -r 's/_/ /g;s/  */ /g;/[=*-]{5,}/d' \
                | ~/trnlp/tokenizer/tr-tokenize.py \
                | gzip -c \
                > $tf" 
            if [[ $? -eq 124 ]]; then
                echo -e "Timout processing $f" >> tokenize.log
                rm -f $tf
            elif [[ $? -eq 0 ]]; then
                echo -e "Convertion failed $f" >> tokenize.log
                rm -f $tf
            fi
        done
    done
done
