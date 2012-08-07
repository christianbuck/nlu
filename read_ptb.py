#!/usr/bin/env python

import sys
from collections import defaultdict
import re
import json
from nltk.tree import Tree

def read_trees(filename, treelist, check=True):
    buffer = []
    for line in open(filename):
        if not line.strip():
            continue
        if line.startswith("(") and buffer:
            tree = ' '.join(buffer)
            tree = re.sub('\s+', ' ', tree)
            treelist.append(tree)
            buffer = []
        buffer.append(line.rstrip())
    if buffer:
        tree = ' '.join(buffer)
        tree = re.sub('\s+', ' ', tree)
        treelist.append(tree)

    if check:
        for idx, tree in enumerate(treelist):
            try:
                t = Tree.parse(tree)
                s = "  ".join(t.leaves())
            except ValueError:
                assert False, "f: %s, i: %s, t: %s" %(filename, idx, tree)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='+', help="input files")
    args = parser.parse_args(sys.argv[1:])

    trees = defaultdict(list)
    for idx, filename in enumerate(args.infiles):
        filenr = filename[4:8]
        read_trees(filename, trees[filenr])

    print json.dumps(trees, indent=2)
