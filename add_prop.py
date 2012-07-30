#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re

'''
we want this:
"prop": [{
         "raw": "disappoint-v disappoint.01 ----- 2:0-rel 3:0-ARG1 4:1;12:1-ARG0 0:1*3:0-LINK-PCR",
     "roleset": "disappoint.01",
    "baseform": "disappoint",
     "basepos": "v",
  "inflection": "-----",
        "args": [["rel", "2:0", "disappointed-3"], ["ARG1", "3:0", "analysts-1"], ["ARG0", "4:1;12:1", "showed-11"], ["LINK-PCR", "0:1*3:0", null]]
}]

'''

def read_propbank(filename):
    '''
    Propbank looks like this:

    wsj/00/wsj_0003.mrg 0 14 gold cause.01 pnp3a 0:3-ARG0 14:0-rel 15:2-ARG1
    wsj/00/wsj_0003.mrg 0 26 gold expose.01 p---p 26:0-rel 28:1-ARG2-to 30:3-ARGM-TMP 22:1,24:0,25:1*27:0-ARG1
    wsj/00/wsj_0003.mrg 0 37 gold report.01 vp--a 36:1-ARG0 37:0-rel 0:4*39:0-ARG1
    wsj/00/wsj_0003.mrg 1 11 gold enter.01 vn-3a 10:1-ARG0 11:0-rel 12:1-ARG1
    '''
    pb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.match('^wsj/\d+/wsj_(\d+).mrg (\d+) \d+ gold (.*)$', line)
        if not m:
            print line
        fileId, sentNr, raw = m.groups()
        pb[fileId][sentNr].append(raw)
    return pb


def read_onprop(filename):
    '''
    Ontonotes PB looks like this:

    nw/wsj/00/wsj_0002@0002@wsj@nw@en@on 0 16 gold name-v name.01 ----- 16:0-rel 17:0-ARG1 18:2-ARG2 17:0*17:0-LINK-PCR
    '''
    pb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.search('wsj_(\d+)@\S+ (\d+) \d+ gold (.*)$', line)
        if not m:
            print line
        print m.groups()
        fileId, sentNr, raw = m.groups()
        pb[fileId][sentNr].append(raw)

    return pb

def parse_onprop(raw_prop):
    """ input like this:
    disappoint-v disappoint.01 ----- 2:0-rel 3:0-ARG1 4:1;12:1-ARG0 0:1*3:0-LINK-PCR
    join-v join.01 ----- 8:0-rel 0:2-ARG0 7:0-ARGM-MOD 9:1-ARG1 11:1-ARGM-PRD 15:1-ARGM-TMP
    """
    re_onprop = re.compile(r'^(?P<baseform>\w+)-(?P<basepos>\w) (?P<roleset>\w+[.]\d+) (?P<inflection>\S+) (?P<args>.*)$')
    m = re_onprop.match(raw_prop.strip())
    assert m, "no match: %s" %raw_prop
    m.groupdict()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('probbank', action='store', help="prop.txt file")
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    args = parser.parse_args(sys.argv[1:])

    pb = read_onprop(args.probbank)
    for fileid in pb:
        for sentNr in pb[fileid]:
            for prop in pb[fileid][sentNr]:
                parse_onprop(prop)
    #print pb
    sys.exit()

    pb = read_propbank(args.probbank)

    # json filename should look like this:
    # /home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/01/wsj_0125.1.json
    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', args.json).groups()
    print docId, sentNr

    assert docId in pb
    #print pb[docId].keys()
    #assert sentNr in pb[docId]

    data = json.load(open(args.json))

    pb_dict = {'raw': pb[docId][sentNr]}

    re_prop = re.compile(r'')


    data['propbank_raw'] = pb_dict
    json.dump(open(args.jsonout,'w'),data)


    #/home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/00/wsj_0036.prop


        #print m.groups()


    #for linenr, line in enumerate(sys.stdin):
    #    line = line.strip().split()
