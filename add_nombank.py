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

def read_nombank(filename):
    '''
    nombank looks like this:

    wsj/00/wsj_0012.mrg 15 13 % 01 0:3-ARG1 13:0-rel
    wsj/00/wsj_0012.mrg 3 18 % 01 11:2-ARG1 16:0-Support 18:0-rel
    wsj/00/wsj_0016.mrg 0 14 % 01 0:3-ARG1 12:0-Support 14:0-rel
    wsj/00/wsj_0016.mrg 3 13 % 01 0:1-ARG1 10:0-Support 13:0-rel
    wsj/00/wsj_0016.mrg 4 6 % 01 0:2-ARG1 4:0-Support 6:0-rel
    wsj/00/wsj_0018.mrg 19 19 % 01 19:0-rel 20:1-ARG1

    '''
    nb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.match(r'^wsj/\d+/wsj_(\d+).mrg (\d+) (\d+) (\S+) (\d+) (.*)$', line)
        assert m, "strange line %s\n" %line
        fileId, sentNr, tokenNr, lemma, frame, args = m.groups()
        sentNr = int(sentNr)
        nb[fileId][sentNr].append({'tokenNr': tokenNr,
                                   'baseform' :lemma, \
                                   'frame' :frame, \
                                   'args' : [arg.split('-',1) for arg in args.split()]})
    return nb

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


def is_trace(subtree):
    if subtree.node == '-NONE-' or len(subtree) == 1:
        words = subtree.leaves()
        if len(words) == 1 and re.match(r'.*-\d+$',words[0]):
            return True
    return False

def span_from_treepos(tree, treepos):
    st = SpanTree.parse(str(tree))
    st.convert()
    start = min(st[treepos].leaves())
    end = max(st[treepos].leaves())
    return (start, end)

def process_file(json_filename, nb):
    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', json_filename).groups()
    sentNr = int(sentNr)
    data = json.load(open(json_filename))
    data['nom'] = []

    pt = SpanTree.parse(data['ptbparse'])

    for nb_data in nb[docId][sentNr]:
        args = nb_data['args']
        new_args = []
        for pos, role in args:
            words, start, end = [], None, None
            leaf_id, depth = pt.parse_pos(pos)
            if leaf_id != None and depth != None:
                treepos = pt.get_treepos(leaf_id, depth)
                while is_trace(pt[treepos]):
                    trace_id = int(pt[treepos].leaves()[0].split('-')[-1])
                    print 'looking for trace', trace_id
                    tracepos = pt.find_trace(trace_id)
                    if tracepos != None:
                        print 'trace %s found! Here:', tracepos
                        print pt[tracepos].pprint()
                        treepos = tracepos
                    else:
                        break # could not follow trace

                words = pt[treepos].leaves()
                start, end = span_from_treepos(pt, treepos)

            new_args.append( [role, pos, start, end, ' '.join(words)] )

        nb_data['args'] = new_args
        data['nom'].append(nb_data)

        #print nb_data
    json.dump(data, open(json_filename, 'w'), indent=2, sort_keys=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('nombank', action='store', help="nombank.1.0 file")
    parser.add_argument('json', action='store', nargs='+', help="json input file")
    arguments = parser.parse_args(sys.argv[1:])

    nb = read_nombank(arguments.nombank)

    for filename in arguments.json:
        print filename, '...'
        process_file(filename, nb)
