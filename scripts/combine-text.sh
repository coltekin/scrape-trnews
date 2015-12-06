#!/bin/bash

for d1 in trnews-data/??;do 
    echo $d1
    for d2 in $d1/??;do
        for f in $d2/????????????????.txt-tokenized.gz;do 
            cat $f >> trnews-all-tokenized.txt.gz
        done
    done
done
