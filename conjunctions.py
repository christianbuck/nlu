'''
Attaches conjunction dependents in the AMR based on the dependency parse.
@see: pipeline.loadDepParse() for special handling of conjunctions

@author: Nathan Schneider (nschneid)
@since: 2012-08-08
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept, new_amr_from_old, get_or_create_concept_from_token as amrget

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    nConjOps = {}   # maps conjunction concept variable to its current number of :opX relations
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            if completed[1][(dep["gov_idx"],dep["dep_idx"])]: continue
            i, r, c = dep['dep_idx'], dep["rel"], dep["gov_idx"]
            if r=='conj':
                x = amrget(amr, alignment, c, depParse, completed)
                y = amrget(amr, alignment, i, depParse, completed)
                
                newtriple = (str(x), 'op'+str(nConjOps.setdefault(x,0)+1), str(y))
                nConjOps[x] += 1

                amr = new_amr_from_old(amr, new_triples=[newtriple])

                completed[1][(c,i)] = True

    return depParse, amr, alignment, completed
