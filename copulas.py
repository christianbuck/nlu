'''
Copula constructions and appositives:

For copulas, the predicate goes as the head. 
E.g. for wsj_0077.3, the dependency parse has
  (u'ahead-11', u'nsubj', u'issues-2')
  (u'ahead-11', u'cop', u'were-9')
which is converted to
  (a / ahead
     :domain (i / issues))

Appositive heads are marked as coreferent with 
the modified noun. E.g. in wsj_0001.1,
  (u'N.V.-6', u'appos', u'group-11')
the named entity containing "N.V." is marked with 
the [:-COREF group] relation.

@author: Nathan Schneider (nschneid)
@since: 2012-08-13
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept, new_amr_from_old, get_or_create_concept_from_token as amrget

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
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
            if (h in cop_preds and r.endswith('subj')) or r=='appos':
                x = amrget(amr, alignment, h, depParse, wTags, completed)
                y = amrget(amr, alignment, i, depParse, wTags, completed)  # asserting non-completion here might be bad
                
                if r=='appos':
                    completed[1][(h,i)] = True
                    if '-FALLBACK' in amr.get_concept(str(x)) and '-FALLBACK' not in amr.get_concept(str(y)):
                        x, y = y, x
                
                if x!=y:
                    newtriple = (str(x), '-COREF' if r=='appos' else 'domain', str(y))
                
                amr = new_amr_from_old(amr, new_triples=[newtriple])

    return depParse, amr, alignment, completed

