#!/usr/bin/env python

import sys
import json
from offset import Offset
from brackets import escape_brackets, unescape_brackets

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    arguments = parser.parse_args(sys.argv[1:])

    data = json.load(open(arguments.json))

    cleanstring = escape_brackets(data['text']).split()
    tracestring = escape_brackets(data['treebank_sentence']).split()
    off = Offset(cleanstring, tracestring)

    words = data['words']
    #print 'c:', cleanstring
    #print 't:', tracestring
    for i, w in enumerate(words):
        lemma = escape_brackets(w[0])
        assert len(w) == 2
        adjusted_idx = off.map_to_longer(i)
        assert lemma == cleanstring[i]
        assert lemma == tracestring[adjusted_idx]
        w[1]['idx'] = adjusted_idx

    json.dump(data, open(arguments.jsonout,'w'), indent=2)
