#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip


"""
convert propbank which looks like this:

wsj/00/wsj_0003.mrg 0 5 gold use.01 p---p 4:1-ARGM-TMP 5:0-rel 0:2*6:0-ARG1 7:2-ARG2-PNC
wsj/00/wsj_0003.mrg 0 9 gold make.01 i---a 7:0-ARG0 9:0-rel 10:1-ARG1
wsj/00/wsj_0003.mrg 0 14 gold cause.01 pnp3a 0:3-ARG0 14:0-rel 15:2-ARG1
wsj/00/wsj_0003.mrg 0 26 gold expose.01 p---p 26:0-rel 28:1-ARG2-to 30:3-ARGM-TMP 22:1,24:0,25:1*27:0-ARG1

to Ontopnotes .prop files which look like this:

nw/wsj/00/wsj_0003@0003@wsj@nw@en@on 0 5 gold use-v use.01 ----- 5:0-rel 6:0-ARG1 4:1-ARGM-TMP 7:2-ARG2 0:2*6:0-LINK-PCR
nw/wsj/00/wsj_0003@0003@wsj@nw@en@on 0 9 gold make-v make.01 ----- 9:0-rel 7:0-ARG0 10:1-ARG1
nw/wsj/00/wsj_0003@0003@wsj@nw@en@on 0 14 gold cause-v cause.01 ----- 14:0-rel 0:3-ARG0 15:2-ARG1
nw/wsj/00/wsj_0003@0003@wsj@nw@en@on 0 26 gold expose-v expose.01 ----- 26:0-rel 27:0-ARG1 28:1-ARG2 30:3-ARGM-TMP 25:1*27:0-LINK-PCR
"""


def convert(line):
    fileid = line[0].split('.')[0] # wsj/00/wsj_0003.mrg -> wsj/00/wsj_0003
    filenr = fileid[-4:]           # wsj/00/wsj_0003 -> 0003
    docid = "nw/%s@%s@wsj@nw@en@on" %(fileid, filenr)
    sentnr = line[1]
    wordidx = line[2]
    gold = line[3]
    assert gold == 'gold' # compare specific weight
    baseform = line[4]
    verb, verbsense = baseform.split('.')  # use.01 -> use 01
    cov = line[5] # not used
    args = ' '.join(line[6:])

    return "%s %s %s %s %s-v %s.%s ----- %s" %(docid, sentnr, wordidx, gold, verb, verb, verbsense, args)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('propbank', action='store', help="propbank.txt")
    parser.add_argument('docid', action='store', help="propbank.txt")
    args = parser.parse_args(sys.argv[1:])

    docid = args.docid.split('.')[0]
    sys.stderr.write('looking for docid %s\n' %(docid))

    for linenr, line in enumerate(open(args.propbank)):
        if not docid in line:
            continue
        print convert(line.strip().split())
