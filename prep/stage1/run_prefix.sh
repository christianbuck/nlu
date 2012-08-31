#!/bin/bash

# Pipeline Code
#SRC=/nfs/guest/yaqiny/Dropbox/Code/OntonotesUtil/ontonotes-db-tool-v0.999b/src
#SRC=/home/buck/Dropbox/isi/OntonotesUtil/ontonotes-db-tool-v0.999b/src
ONDBTOOL=/nfs/nlg/semmt/tools/eng2amr/prepro_pipeline/ontonotes-db-tool-v0.999b
MYCONFIG=$ONDBTOOL/myconfig


# Ontonotes Data
#ONTONOTES=/nfs/nlg/semmt/data/ontonotes/ontonotes-release-4.0/data/files/data
#ONTONOTES=/home/buck/corpora/ontonotes-release-4.0/data/files/data
ONTONOTES=/nfs/nlg/semmt/data/on_fixed/ontonotes-release-4.0/data/files/data


# Stanford Headrules
#HEADRULES=/home/buck/Dropbox/isi/OntonotesUtil/ontonotes-db-tool-v0.999b/data/headrules.txt
#HEADRULES=$ONDBTOOL/data/headrules.txt

#CORPORA="parse coref sense name parallel prop speaker"
GENRE="english-nw-wsj"
#PREFIX="00"
#SUFFIX="00"

# Granularity?
#GRAN=source

wsj=/nfs/nlg/semmt/data/on_fixed/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj
files_with_coref=WSJFilesWithCoref.txt
XML_name_entity=/nfs/nlg/semmt/data/bbn_fixed/bbn-pcet/data/WSJtypes-subtypes

export PYTHONPATH=".:$ONDBTOOL/src"

#for PREFIX in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24;
for PREFIX in $*;
do
    python Predicate.py $wsj $files_with_coref $XML_name_entity -c $MYCONFIG corpus.data_in=$ONTONOTES corpus.load=$GENRE corpus.prefix=$PREFIX corpus.suffix="" corpus.banks="parse prop name coref"
done

#python $SRC/NathanUtil.py $MYCONFIG
#python $SRC/MyUtil.py -c $MYCONFIG corpus.data_in=$ONTONOTES corpus.load=$GENRE corpus.prefix=$PREFIX corpus.suffix=$SUFFIX corpus.banks=$CORPORA corpus.granularity=$GRAN
#python $SRC/MyUtil.py -c $MYCONFIG corpus.data_in=$ONTONOTES corpus.load=$GENRE corpus.prefix=$PREFIX corpus.suffix=$SUFFIX corpus.banks="parse prop"
#python $SRC/Predicate.py -c $MYCONFIG corpus.data_in=$ONTONOTES corpus.load=$GENRE corpus.prefix=$PREFIX corpus.suffix="01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24" corpus.banks="parse prop name coref"
# python $SRC/Predicate.py -c $MYCONFIG corpus.data_in=$ONTONOTES corpus.load=$GENRE corpus.prefix=$PREFIX corpus.suffix="24" corpus.banks="parse prop name coref"
#01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
