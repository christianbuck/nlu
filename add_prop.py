#!/usr/bin/env python

import sys
from collections import defaultdict
import json
import re
from spantree import SpanTree
import os

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

def read_propbank(filename):
    '''
    Propbank looks like this:

    wsj/00/wsj_0003.mrg 0 14 gold cause.01 pnp3a 0:3-ARG0 14:0-rel 15:2-ARG1
    wsj/00/wsj_0003.mrg 0 26 gold expose.01 p---p 26:0-rel 28:1-ARG2-to 30:3-ARGM-TMP 22:1,24:0,25:1*27:0-ARG1
    wsj/00/wsj_0003.mrg 0 37 gold report.01 vp--a 36:1-ARG0 37:0-rel 0:4*39:0-ARG1
    wsj/00/wsj_0003.mrg 1 11 gold enter.01 vn-3a 10:1-ARG0 11:0-rel 12:1-ARG1
    '''
    pb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.match('^wsj/\d+/wsj_(\d+).mrg (\d+) \d+ gold (.*)$', line)
        if not m:
            print line
        fileId, sentNr, raw = m.groups()
        pb[fileId][int(sentNr)].append(raw)
    return pb


def read_onprop(filename):
    '''
    Ontonotes PB looks like this:

    nw/wsj/00/wsj_0002@0002@wsj@nw@en@on 0 16 gold name-v name.01 ----- 16:0-rel 17:0-ARG1 18:2-ARG2 17:0*17:0-LINK-PCR
    '''
    pb = defaultdict(lambda: defaultdict(list))

    for line in open(filename):
        m = re.search('wsj_(\d+)@\S+ (\d+) \d+ gold (.*)$', line)
        if not m:
            print line
        #print m.groups()
        fileId, sentNr, raw = m.groups()
        pb[fileId][int(sentNr)].append(raw)

    return pb

def parse_onprop(raw_prop):
    """ input like this:
    disappoint-v disappoint.01 ----- 2:0-rel 3:0-ARG1 4:1;12:1-ARG0 0:1*3:0-LINK-PCR
    join-v join.01 ----- 8:0-rel 0:2-ARG0 7:0-ARGM-MOD 9:1-ARG1 11:1-ARGM-PRD 15:1-ARGM-TMP
    """
    re_onprop = re.compile(r'^(?P<baseform>\w+)-(?P<basepos>\w) (?P<frame>\w+[.](\d+|XX)) (?P<inflection>\S+) (?P<args>.*)$')
    m = re_onprop.match(raw_prop.strip())
    assert m, "no match: %s" %raw_prop
    d = m.groupdict()
    d['args'] = [arg.split('-',1) for arg in d['args'].split()]
    return d

def get_trace(subtree, recursive=False):
    '''
    If the yield of a given subtree consists of empty elements, one of them with 
    a consituent pointer index (e.g. *-10 or *T*-10), returns that token. 
    Otherwise, returns None. 
    
    If 'recursive' is True: checks whether the subtree's entire yield consists of 
    empty elements, exactly one of which has a constituent pointer; if so, returns 
    that element, otherwise returns None.
    
    If 'recursive' is False: returns the subtree's yield iff the subtree is a 
    preterminal for an empty element with a constituent pointer, and None otherwise.
    '''
    re_trace = re.compile(r'.*-\d+$')
    if subtree.node == '-NONE-' or subtree.height() == 2:   # nschneid: isn't the first condition redundant, i.e. all '-NONE-' nodes have height 2?
        words = ' '.join(subtree.leaves())
        if re_trace.match(words):
            return words
    elif recursive: # check if all subtrees of height 2 point to empty elements
        st_h2 = list(subtree.subtrees(filter=lambda t: t.height()==2))
        st_none = list(subtree.subtrees(filter=lambda t: t.node=='-NONE-'))
        if st_h2 == st_none:
            # if we have only one trace follow that one
            traces = [get_trace(st) for st in st_h2 if re_trace.match(' '.join(st.leaves()))]
            if len(traces) == 1:
                return traces[0]
    return None

def span_from_treepos(tree, treepos):
    st = SpanTree.parse(str(tree))
    st.convert()
    start = min(st[treepos].leaves())
    end = max(st[treepos].leaves())
    return (start, end)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('probbank', action='store', help="prop.txt file")
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    parser.add_argument('-nonrecursive', action='store_true')
    arguments = parser.parse_args(sys.argv[1:])
    recursive = not arguments.nonrecursive

    pb = None
    if os.path.isfile(arguments.probbank):
        pb = read_onprop(arguments.probbank)
    else:
        prop_bank_prob = arguments.probbank.replace(".prop",".pprop")
        assert os.path.isfile(prop_bank_prob)
        pb = read_onprop(prop_bank_prob)
    assert pb != None

    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', arguments.json).groups()
    sentNr = int(sentNr)
    data = json.load(open(arguments.json))
    data['prop'] = []

    pt = SpanTree.parse(data['goldparse'])

    

    for propS in pb[docId][sentNr]:
        prop = parse_onprop(propS)
        args = prop['args']

	# TODO: concatenated arguments (comma-separated positions used if the argument is not a constituent)
	# currently these appear in the output with null start and end positions
        
        
        support2main = {}
	# for LINK-PCR and LINK-SLC arguments, there is a relativizer or empty element which 
	# I am calling a "support" node; this "support" is associated with a normal argument 
	# and the link associates it with the main node. In the output, supporting nodes are 
	# moved to a special slot within the argument, replaced in the normal slot by the 
	# corresponding main node, and the LINK entries are removed.
        # see wsj_0003.0 for an example ('workers' at 25:1 vs. '*' at 27:0 as the ARG1 of expose.01)
        for position, role in args:
            if role in ['LINK-PCR','LINK-SLC']:
                mainNode, supportNode = position.split('*')[:2] # TODO: sometimes more than 2 chain members, e.g. in wsj_0003.10
		assert support2main.setdefault(supportNode, mainNode)==mainNode
        
        new_args = []
        for position, role in args: # update the arguments with token span offsets where possible
	    if role in ['LINK-PCR','LINK-SLC']: continue # exclude the link entries themselves from the output
            words, start, end, support = [], None, None, []
            
            leaf_id, depth = pt.parse_pos(position)
            if leaf_id is not None and depth is not None:
                treepos = pt.get_treepos(leaf_id, depth)
		support = [position]+list(span_from_treepos(pt, treepos))+[' '.join(pt[treepos].leaves())]

                if position in support2main:
                    mainNode = support2main[position]   # use mapping from a LINK entry
                    # look up node in the tree, convert to offsets
                    pt = SpanTree.parse(data["goldparse"])  # TODO: what if it is a non-OntoNotes (PTB) tree?
                    leaf_id, depth = pt.parse_pos(mainNode)
                    treepos = pt.get_treepos(leaf_id, depth)
                    position = mainNode

                trace = get_trace(pt[treepos], recursive=recursive)
                while trace is not None:    # follow trace pointer to another constituent
                    trace_id = int(trace.split('-')[-1])
                        
                    # attempt to follow trace pointer to a consituent
                    tracepos = pt.find_trace(trace_id)
                    if tracepos is not None:
	                start, end = span_from_treepos(pt, treepos)
			if support[-3:-1]!=[start,end]:
                            support.extend([start,end,' '.join(pt[treepos].leaves())])
                        treepos = tracepos
                    else:
                        break # could not follow trace
                        
                    # we have possibly arrived at another trace
                    trace = get_trace(pt[treepos], recursive=recursive)

                words = pt[treepos].leaves()
                start, end = span_from_treepos(pt, treepos)
            else: # position was not number:number
                pass

            # argument (possibly with token offsets)
            new_arg = [role, position, start, end, ' '.join(words)]
	    new_arg.append(support if support!=new_arg[1:] else [])
            new_args.append(new_arg)

        prop['args'] = new_args
        data['prop'].append(prop)

    json.dump(data, open(arguments.jsonout, 'w'), indent=2, sort_keys=True)
