#!/usr/bin/env python2.7
'''
Driver and utilities for English-to-AMR pipeline.
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

from dev.amr.amr import Amr
from alignment import Alignment

def main(sentenceId):
    # load dependency parse from sentence file
    depParse = loadDepParse(sentenceId)
    
    # pipeline steps
    import nes, adjsAndAdverbs

    # initialize input to first pipeline step
    completed = [False]*len(depParse)
    amr = Amr()
    alignments = Alignment()

    # serially execute pipeline steps
    for m in [nes, adjsAndAdverbs]:
        depParse, amr, alignments, completed = m.main(sentenceId, depParse, amr, alignments, completed)
        print(repr(amr), file=sys.stderr)
        print(alignments, completed, file=sys.stderr)
        print(amr, file=sys.stderr)

    # TODO: output

def token2concept(t):
    return re.sub(r'[^A-Za-z0-9-]', '', t).lower() or '??'


def loadBBN(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['bbn_ne']

def loadDepParse(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        deps_concise = json.load(jsonF)['stanford_dep']
        deps = []
        for entry in deps_concise:
            while len(deps)<entry['dep_idx']:
                deps.append(None)   # dependency root, puncutation, or function word incorporated into a dependecy relation
            deps.append(entry)
        return deps

def choose_head(tokenIndices, depParse):
    # restricted version of least common subsumer:
    # assume that for every word in the NE, 
    # all words on the ancestor path up to the NE's head 
    # are also in the NE
    frontier = set(tokenIndices)    # should end up with just (the head)
    for itm in set(frontier):
        if depParse[itm+1]['gov_idx']-1 in tokenIndices:
            # subtract 1 to account for dependency root
            frontier.remove(itm)
    assert len(frontier)==1
    return next(iter(frontier))
    

def new_concept(concept, amr, alignment=None, alignedToken=None):
    # new variable
    x = len(amr.node_to_concepts)
    
    amr.node_to_concepts[str(x)] = concept
    
    if alignedToken is not None:
        alignment.link(x, alignedToken)
    
    return x    # variable, as an integer


if __name__=='__main__':
    sentId = sys.argv[1]
    main(sentId)
