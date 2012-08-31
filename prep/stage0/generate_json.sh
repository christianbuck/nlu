#!/bin/bash

#Steps to generate all the json files

SOURCE=/nfs/nlg/semmt/data/ontonotes/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj
TARGET=/nfs/nlg/semmt/data/on_fixed/ontonotes-release-4.0/data/files/data/english/annotations/nw
NOMBANK=/nfs/nlg/semmt/data/nombank/v1.0/nombank.1.0

#### 1. Start with plain ontonotes

cp -r  $SOURCE $TARGET
DATA=$TARGET/wsj

#### 2. Extract sentences from .onf files:

for f in $DATA/*/*.onf
do 
    echo $f
    cat $f | ./onf2txt.py > ${f/.onf/.txt}
done

#### 3. Run stanford core NLP on text files. 
# this generates one .json file per text files (i.e. per document)

pushd /nfs/nlg/semmt/tools/stanford-corenlp-python
for f in $DATA/*
do 
    ./parse_txt.py ${f}/*.txt
done
popd

#### 4. Fix some Ontonotes errors
#### 4.1 re-generate .parse files as some are missing in ontonotes

for f in $DATA/*/*.onf
do
    PARSEFILE=${f/.onf/.parse}
    if [ ! -f $PARSEFILE ]
    then
        echo $f
        cat $f | ./onf2txt.py > $PARSEFILE
    fi
done

#### 5. Generate .nom files from NomBank
./distribute-nombank.py $NOMBANK $DATA

### ????
for f in ~/semmt/users/cbuck/data/??/*/*/*.onf; do echo $f; ~/semmt/users/cbuck/bin/onf2txt.py < $f > ${f/.onf/.txt}; done
pushd ~/semmt/tools/stanford-corenlp-python
for f in ~/semmt/users/cbuck/data/nw/wsj/00/; do echo $f; nice ./parse_txt.py ${f}/*.txt; done
for f in ~/semmt/users/cbuck/data/??/*/*/; do echo $f; nice ./parse_txt.py ${f}/*.txt; done
popd

