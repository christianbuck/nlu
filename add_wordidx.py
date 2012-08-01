#!/usr/bin/env python

import sys
import json
from offset import Offset

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    arguments = parser.parse_args(sys.argv[1:])

    data = json.load(open(arguments.json))

    cleanstring = data['text'].split()
    tracestring = data['treebank_sentence'].split()
    off = Offset(cleanstring, tracestring)

    words = data['words']
    #print 'c:', cleanstring
    #print 't:', tracestring
    for i, w in enumerate(words):
        assert len(w) == 2
        adjusted_idx = off.map_to_longer(i)
        assert w[0] == cleanstring[i]
        assert w[0] == tracestring[adjusted_idx]
        w[1]['idx'] = adjusted_idx

    json.dump(data, open(arguments.jsonout,'w'), indent=2)
