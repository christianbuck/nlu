'''
Attaches conjunction dependents in the AMR based on the dependency parse.
@see: pipeline.loadDepParse() for special handling of conjunctions

@author: Nathan Schneider (nschneid)
@since: 2012-08-08
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr

import pipeline
from pipeline import new_concept

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    nConjOps = {}   # maps conjunction concept variable to its current number of :opX relations
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            if completed[1][(dep["gov_idx"],dep["dep_idx"])]: continue
            i, r, c = dep['dep_idx'], dep["rel"], dep["gov_idx"]
            if r=='conj':
                x = alignment[:c] # index of variable associated with i's head (the conjunction), if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][c]
                    w = depParse[c][0]["dep"]  # modifier token
                    x = new_concept(pipeline.token2concept(w), amr, alignment, c)
                    completed[0][c] = True
                y = alignment[:i] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept(pipeline.token2concept(dep["dep"]), amr, alignment, i)
                    completed[0][i] = True
                
                newtriple = (str(x), 'op'+str(nConjOps.setdefault(x,0)+1), str(y))
                nConjOps[x] += 1

                amr = Amr.from_triples(amr.triples(instances=False)+[newtriple], amr.node_to_concepts)

                completed[1][(c,i)] = True

    return depParse, amr, alignment, completed
