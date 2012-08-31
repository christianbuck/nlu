#!/usr/bin/env python

'''
We are looking for such structures:

Tree:
-----
    (TOP (S (SBAR-ADV (IN Although)
    ...
'''

import sys
import os
from nltk.tree import Tree
#sys.exit()

mode = 0
parse = ""

first_tree = True
for line in sys.stdin:
    #print 'mode:', mode
    line = line[:-1] # remove newline

    if line == 'Leaves:':
        assert mode == -2

        if mode == -2:
            t = Tree.parse(parse)
            assert t
            if not first_tree:
                print ''
            first_tree = False
            print t.pprint()
            parse = ""
        mode = 0
        continue

    if line.startswith('Tree:'):
        mode -= 1
    elif line == '-----':
        mode -= 1
    else:
        assert abs(mode) < 3
        if mode == -2:
            if line.startswith('    '):
                line = line[4:]
            if not line.strip():
                continue
            parse += line.rstrip() + "\n"
