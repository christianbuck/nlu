#!/usr/bin/env python

# check if parse from .onf is equal to parse obtained from penn treebank

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    arguments = parser.parse_args(sys.argv[1:])

    data = json.load(open(arguments.json))

    ptb = Tree.parse(data['ptbparse'])
    onf = Tree.parse(data['goldparse'])

    print pbt == onf
