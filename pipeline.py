#!/usr/bin/env python2.7
'''
Driver and utilities for English-to-AMR pipeline.
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr
from alignment import Alignment

def main(sentenceId):
    # TODO: load dependency parse from sentence file
    
    # pipeline steps
    import adjsAndAdverbs

    # initialize input to first pipeline step
    completed = [False]*len(depParse)
    amr = Amr()
    alignments = Alignment()

    # serially execute pipeline steps
    for m in [adjsAndAdverbs]:
        depParse, amr, alignments, completed = m.main(sentenceId, depParse, amr, alignments, completed)

    # TODO: output

def token2concept(t):
    return re.sub(r'[^A-Za-z0-9-]', '', t) or '??'

if __name__=='__main__':
    sentId = sys.argv[1]
    main(sentId)
