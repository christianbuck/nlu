'''
Copula constructions: the predicate goes as the head. 
E.g. for wsj_0077.3, the dependency parse has
  (u'ahead-11', u'nsubj', u'issues-2')
  (u'ahead-11', u'cop', u'were-9')
which is converted to
  (a / ahead
     :domain (i / issues))

@author: Nathan Schneider (nschneid)
@since: 2012-08-13
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept, new_amr_from_old

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    cop_preds = set()
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            i, r, h = dep["dep_idx"], dep["rel"], dep["gov_idx"]
            if completed[1][(h,i)]: continue
            if r=='cop':
                cop_preds.add(h)
                completed[1][(h,i)] = True
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            i, r, h = dep["dep_idx"], dep["rel"], dep["gov_idx"]
            if h in cop_preds and r.endswith('subj'):
                x = alignment[:h] # index of variable associated with i's head, if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][h]
                    x = new_concept(pipeline.token2concept(ww[h]), amr, alignment, h)
                    completed[0][h] = True
                y = alignment[:i] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept(pipeline.token2concept(dep["dep"]), amr, alignment, i)
                    completed[0][i] = True
                
                if x!=y:
                    newtriple = (str(x), 'domain', str(y))
                
                amr = new_amr_from_old(amr, new_triples=[newtriple])

    return depParse, amr, alignment, completed

