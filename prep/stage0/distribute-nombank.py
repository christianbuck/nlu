#!/usr/bin/env python2.7
'''
Splits the NomBank annotations into one file per document.

Note that the NomBank file is ordered alphabetically by 
predicate, so not all of every output file's lines will 
be written together.

Args: <nombank_file> <WSJ_root_directory>
E.g., the first entry will go in the file
  <WSJ_root_directory>/00/wsj_0005.nom

To delete the output files:
  $ rm <WSJ_root_directory>/??/wsj_????.nom

@author: Nathan Schneider (nschneid)
@since: 2012-08-31
'''
from __future__ import print_function
import os, sys, re

nombankFile = sys.argv[1]
#/nfs/nlg/semmt/data/nombank/v1.0/nombank.1.0

wsj = sys.argv[2]

with open(nombankFile) as inF:
    for ln in inF:
        # e.g. wsj/00/wsj_0005.mrg 0 16 % 01 16:0-rel 17:0-Support 18:1-ARG1
        wsjFile = ln[:-1].split()[0]
        outFile = wsjFile.replace('.mrg','.nom').replace('wsj/',wsj+'/')
        with open(outFile, 'a') as outF:
            outF.write(ln)
            print(outFile, file=sys.stderr)
