#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re
from spantree import SpanTree

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
        pb[fileId][int(sentNr)].append(raw)
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
        #print m.groups()
        fileId, sentNr, raw = m.groups()
        pb[fileId][int(sentNr)].append(raw)

    return pb

def parse_onprop(raw_prop):
    """ input like this:
    disappoint-v disappoint.01 ----- 2:0-rel 3:0-ARG1 4:1;12:1-ARG0 0:1*3:0-LINK-PCR
    join-v join.01 ----- 8:0-rel 0:2-ARG0 7:0-ARGM-MOD 9:1-ARG1 11:1-ARGM-PRD 15:1-ARGM-TMP
    """
    re_onprop = re.compile(r'^(?P<baseform>\w+)-(?P<basepos>\w) (?P<roleset>\w+[.]\d+) (?P<inflection>\S+) (?P<args>.*)$')
    m = re_onprop.match(raw_prop.strip())
    assert m, "no match: %s" %raw_prop
    d = m.groupdict()
    d['args'] = [arg.split('-',1) for arg in d['args'].split()]
    return d


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('probbank', action='store', help="prop.txt file")
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    arguments = parser.parse_args(sys.argv[1:])

    pb = read_onprop(arguments.probbank)
    #print pb

    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', arguments.json).groups()
    sentNr = int(sentNr)
    data = json.load(open(arguments.json))
    data['prop'] = []

    pt = SpanTree.parse(data['goldparse'])
    #print list(enumerate(pt.leaves()))
    #print pt.pprint()

    for prop in pb[docId][sentNr]:
        pb_data = parse_onprop(prop)
        args = pb_data['args']
        new_args = []
        for pos, role in args:
            words, start, end = '', None, None
            leaf_id, depth = pt.parse_pos(pos)
            if leaf_id != None and depth != None:
                subtree = pt.subtree_from_pos(leaf_id, depth)
                print 'node:', subtree.node
                if subtree.node == '-NONE-':
                    leaves = subtree.leaves()
                    if len(leaves) == 1 and re.match(r'.*-\d+$',leaves[0]):
                        trace_id = int(leaves[0].split('-')[-1])
                        print 'looking for trace', trace_id
                        tracepos = pt.find_trace(trace_id)
                        if tracepos != None:
                            print 'trace %s found! Here:', tracepos
                            words = ' '.join(pt[tracepos].leaves())
                            st = SpanTree.parse(str(pt))
                            st.convert()
                            start = min(st[tracepos].leaves())
                            end = max(st[tracepos].leaves())
                else:
                    words = ' '.join(subtree.leaves())
                    start, end = pt.span_from_pos(leaf_id, depth)
            new_args.append( [role, pos, start, end, words] )

        pb_data['args'] = new_args
        data['prop'].append(pb_data)

        print pb_data
    json.dump(data, open(arguments.jsonout, 'w'), indent=2)

    #print json.dumps(data, indent=2)

    #print pt.span_from_pos("1:0")

    sys.exit()


    #print data.keys()
    #print docId, sentNr
    #print pb[docId].keys()
    #assert sentNr in pb[docId]

    #print pb

    pb = read_propbank(args.probbank)

    # json filename should look like this:
    # /home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/01/wsj_0125.1.json

    pb_dict = {'raw': pb[docId][sentNr]}

    re_prop = re.compile(r'')


    data['propbank_raw'] = pb_dict
    #json.dump(open(args.jsonout,'w'),data)
    json.dump(data, open(args.jsonout, 'w'), indent=2)


    #/home/buck/corpora/ontonotes-release-4.0/data/files/data/english/annotations/nw/wsj/00/wsj_0036.prop


        #print m.groups()


    #for linenr, line in enumerate(sys.stdin):
    #    line = line.strip().split()
