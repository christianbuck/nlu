#!/usr/bin/env python

import sys
import json
import re

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('ptb', action='store', help="ptb.json file")
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    parser.add_argument('-verbose', action='store_true')
    arguments = parser.parse_args(sys.argv[1:])

    treebank = json.load(open(arguments.ptb))

    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', arguments.json).groups()
    #print treebank.keys()
    #print docId
    #int(docId)
    sentNr = int(sentNr)
    data = json.load(open(arguments.json))

    if arguments.verbose:
        from nltk.tree import Tree
        sys.stderr.write("text:\n"), data['text']
        sys.stderr.write("%s\n" %(treebank[docId][sentNr]))

        t = Tree.parse(treebank[docId][sentNr])
        sys.stderr.write("%s\n" %(" ".join(t.leaves())))

    assert docId in treebank
    #print treebank[docId]
    assert int(sentNr) < len(treebank[docId])

    data['ptbparse'] = treebank[docId][sentNr]
    json.dump(data, open(arguments.jsonout, 'w'), indent=2, sort_keys=True)
