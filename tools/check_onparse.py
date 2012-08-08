#!/usr/bin/env python

# check if parse from .onf is equal to parse obtained from penn treebank

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re
from nltk.tree import Tree

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    arguments = parser.parse_args(sys.argv[1:])

    data = json.load(open(arguments.json))

    ptb = Tree.parse(data['ptbparse'])
    onf = Tree.parse(data['goldparse'])

    equal = ptb[0].pprint() == onf[0].pprint()
    if not equal:
        print "0 parses from pbt and .onf differ in %s" %arguments.json
    if equal:
        print "1 parses from pbt and .onf do NOT differ in %s" %arguments.json
        #print ptb[0].pprint()
        #print onf[0].pprint()
