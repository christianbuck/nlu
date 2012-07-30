#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re

'''
Propbank looks like this:

wsj/00/wsj_0003.mrg 0 14 gold cause.01 pnp3a 0:3-ARG0 14:0-rel 15:2-ARG1
wsj/00/wsj_0003.mrg 0 26 gold expose.01 p---p 26:0-rel 28:1-ARG2-to 30:3-ARGM-TMP 22:1,24:0,25:1*27:0-ARG1
wsj/00/wsj_0003.mrg 0 37 gold report.01 vp--a 36:1-ARG0 37:0-rel 0:4*39:0-ARG1
wsj/00/wsj_0003.mrg 1 11 gold enter.01 vn-3a 10:1-ARG0 11:0-rel 12:1-ARG1


'''

def read_propbank(filename):
    pb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.match('wsj/\d+/wsj_(\d+).mrg (\d+) \d+ gold .*', line)
        if not m:
            print line
        fileId, sentNr = m.groups()
        pb[fileId][sentNr].append(line)
    return pb

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('probbank', action='store', help="prop.txt file")
    parser.add_argument('json', action='store', help="json file")
    args = parser.parse_args(sys.argv[1:])

    pb = read_propbank(args.probbank)

    # json filename should look like this:
    # /home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/01/wsj_0125.1.json
    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', args.json).groups()
    print docId, sentNr

    assert docId in pb
    #print pb[docId].keys()
    #assert sentNr in pb[docId]

    data = json.load(open(args.json))
    data['propbank_raw'] = pb[docId][sentNr]
    json.dump(open(args.json,'w'),data)


    #/home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/00/wsj_0036.prop


        #print m.groups()


    #for linenr, line in enumerate(sys.stdin):
    #    line = line.strip().split()
