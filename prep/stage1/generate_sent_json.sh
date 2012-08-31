#!/bin/bash

SCRIPTDIR=stage1b
DATADIR=/nfs/nlg/semmt/data/on_fixed/ontonotes-release-4.0/data/files/data/english/annotations/nw
#NOMBANK=/nfs/nlg/semmt/data/nombank/v1.0/nombank.1.0  # stage0 now generates .nom files, so this is not needed
PTBJSON=/nfs/nlg/semmt/data/ptb.json


#3for PREFIX in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24;
for PREFIX in $*; do
    ./run_prefix.sh $PREFIX

    for f in $DATADIR/wsj/${PREFIX}/wsj_????.*.json; do
        PROPFILE=`echo $f | sed 's/.[0-9]*.json/.prop/'`
        echo $f, $PROPFILE

        $SCRIPTDIR/add_wordidx.py $f $f
        $SCRIPTDIR/add_ptb.py $PTBJSON $f $f
        $SCRIPTDIR/add_dep.py $f $f                     # requires .dep and .dep_basic files

        NOMFILE=`echo $f | sed 's/.[0-9]*.json/.nom/'`
        echo $f, $NOMFILE
        $SCRIPTDIR/add_nombank.py $NOMFILE $f
	
        $SCRIPTDIR/add_timex.py $f
        $SCRIPTDIR/add_prop.py $PROPFILE $f $f
        $SCRIPTDIR/adjust_coref.py $f $f
        $SCRIPTDIR/adjust_bbn.py $f $f
    done
done
