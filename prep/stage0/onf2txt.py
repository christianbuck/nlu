#!/usr/bin/env python

'''
We are looking for such structures:

Tree:
-----
    (TOP (S (SBAR-ADV (IN Although)
    ...
'''

import sys
from nltk.tree import Tree
#sys.exit()

mode = 0
parse = ""


for line in sys.stdin:
    #print 'mode:', mode
    line = line[:-1] # remove newline

    if line == 'Leaves:':
        assert mode == -2
        if mode == -2:
            pt = Tree.parse(parse)
            parse = " ".join([w for w,pos in pt.pos() if pos not in ['-NONE-','XX']])
            parse = parse.replace('-LRB-', '(')
            parse = parse.replace('-RRB-', ')')
            parse = parse.replace('-LSB-', '[')
            parse = parse.replace('-RSB-', ']')
            parse = parse.replace('-LCB-', '{')
            parse = parse.replace('-RCB-', '}')
            print parse
            parse = ""
            plain_sentence = ""
        mode = 0
        continue

    if line.startswith('Tree:'):
        mode -= 1
    elif line == '-----':
        mode -= 1
    else:
        #print mode, line
        assert abs(mode) < 3
        if mode == -2:
            parse += line.strip() + " "
