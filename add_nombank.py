#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re
from offset import Offset
from brackets import escape_brackets
from spantree import SpanTree
from nltk.tree import Tree

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
        nb[fileId][sentNr].append({'tokenNr':tokenNr,
                                   'baseform' :lemma,
                                   'frame' :'.'.join((lemma,frame)),
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

def tree_to_string(t, include_traces=True, wrap_traces=True):
    """
    given a nktk.tree.Tree return sentence
    if wrap_traces put brackets <> around traces
    """
    words = []
    for w, pos in t.pos():
        if pos not in ['-NONE-','XX']:
            words.append(w)
        elif include_traces:
            if wrap_traces:
                words.append("<%s>"%w)
            else:
                words.append(w)
    return ' '.join(words)


def add_spaces(s1, s2):
    # add spaces to s1 so that it looks like s2
    # ignore everything in brackets
    assert len(s1) <= len(s2)
    out = []
    j = 0 # index in s1
    i = 0 # index in s2
    while i < len(s2):
        #print i, j, out
        if s1[j] == '<': # copy tag from s1
            while s1[j] != '>':
                out.append(s1[j])
                j += 1
            out.append(s1[j]) # append the '>'
            j += 1 # move behind '>'
            continue
        if s2[i] == '<': # skip tag in s2
            while s2[i] != '>':
                i += 1
            i+= 1 # move behind '>'
            continue
        if s1[j] == s2[i]:
            out.append(s1[j])
            j += 1
            i += 1
            continue
        if s2[i] == ' ':
            out.append(' ')
            i += 1
            continue
        else:
            assert False, "weird: \n\t %s \n\t %s\n \n\t %s" %(s1, s2, ''.join(out))

    # maybe close tag
    while j < len(s1) and s1[j] == '<': # copy tag
        while j < len(s1) and s1[j] != '>':
            out.append(s1[j])
            j += 1
        out.append(s1[j])
        j += 1
    out = ''.join(out)
    return out


def split_offsets(s1, s2):
    """
    s2 is a string with more spaces but otherwise the same as s1
    find offsets such that s1[i] = ''.join([s2[j] for j offset[i]])
    """
    w1 = s1.split()
    w2 = s2.split()
    assert len(w1) <= len(w2)
    offsets = defaultdict(list) # old idx -> list of new indices
    j = 0 # index in w2
    for i, w in enumerate(w1):
        merged_word = ''
        while j < len(w2) and merged_word != w:
            merged_word = merged_word + w2[j]
            offsets[i].append(j)
            j += 1
        assert merged_word == w, 'found %s, looking for %s' %(merged_word, w)
    return dict(offsets.items())




def process_file(json_filename, nb):
    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', json_filename).groups()
    sentNr = int(sentNr)
    data = json.load(open(json_filename))
    data['nom'] = []

    # index adjustments for consistency with ontonotes parses
    ptb_tree = Tree.parse(data['ptbparse'])
    ptbstring = tree_to_string(ptb_tree) # wrap traces

    onftree = Tree.parse(data['goldparse'])
    onfstring = tree_to_string(onftree) # wrap traces
    raw_onfstring = tree_to_string(onftree, wrap_traces=False)

    ptbstring_tok = add_spaces(ptbstring, onfstring)

    tokenize_offsets = split_offsets(ptbstring, ptbstring_tok)
    trace_offsets = Offset(ptbstring_tok.split(), onfstring.split(), ignore_braces=True)

    #print ptbstring
    #print ptbstring_tok
    #print onfstring
    #print tokenize_offsets
    #print trace_offsets

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
                #print start, end,

                # adjust of different tokenization
                assert start in tokenize_offsets
                start = min(tokenize_offsets[start])
                assert end in tokenize_offsets
                end = max(tokenize_offsets[end])

                # adjust of inserted traces in ontonotes
                start = trace_offsets.map_to_longer(start)
                end = trace_offsets.map_to_longer(end)
                #print '->', start, end

            phrase = ''
            if words:
                phrase = ' '.join(raw_onfstring.split()[start:end+1])
            new_args.append( [role, pos, start, end, phrase] )

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
        try:
            process_file(filename, nb)
        except AssertionError:
            raise
