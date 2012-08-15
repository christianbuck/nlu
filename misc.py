'''
Attaches miscellaneous remaining edges from the dependency parse: currently
  nn -> :mod-NN
  prep_X -> :prep-X

@author: Nathan Schneider (nschneid)
@since: 2012-08-09
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept, new_amr_from_old, get_or_create_concept_from_token as amrget

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            i, r, h = dep["dep_idx"], dep["rel"], dep["gov_idx"]
            if completed[1][(h,i)]: continue
            if r in ['nn','poss'] or r.startswith('prep_'):
                x = amrget(amr, alignment, h, depParse, completed)
                y = amrget(amr, alignment, i, depParse, completed) # modifier variable
                
                if r=='nn':   # attach as :mod-NN
                    newtriple = (str(x), 'mod-NN', str(y))
                elif r=='poss':
                    newtriple = (str(x), 'poss', str(y))
                else:   # attach with :prep-X relation
                    assert r.startswith('prep_')
                    newtriple = (str(x), r.replace('_','-'), str(y))
                
                
                amr = new_amr_from_old(amr, new_triples=[newtriple])

                completed[1][(h,i)] = True

    '''
    # simplify adverbs to adjectives based on lexicon
    for v in amr.node_to_concepts.keys():
        amr.node_to_concepts[v] = simplify_adv(amr.node_to_concepts[v])
    '''
    
    return depParse, amr, alignment, completed

