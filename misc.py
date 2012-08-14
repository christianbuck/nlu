'''
Attaches miscellaneous remaining edges from the dependency parse: currently
  nn -> :mod-NN
  prep_X -> :prep-X

@author: Nathan Schneider (nschneid)
@since: 2012-08-09
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr

import pipeline
from pipeline import new_concept

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            i, r, h = dep["dep_idx"], dep["rel"], dep["gov_idx"]
            if completed[1][(h,i)]: continue
            if r in ['nn','poss'] or r.startswith('prep_'):
                x = alignment[:h] # index of variable associated with i's head, if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][h]
                    x = new_concept(pipeline.token2concept(ww[h]), amr, alignment, h)
                    completed[0][h] = True
                y = alignment[:i] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept(pipeline.token2concept(dep["dep"]), amr, alignment, i)
                    completed[0][i] = True
                
                if r=='nn':   # attach as :mod-NN
                    newtriple = (str(x), 'mod-NN', str(y))
                elif r=='poss':
                    newtriple = (str(x), 'poss', str(y))
                else:   # attach with :prep-X relation
                    assert r.startswith('prep_')
                    newtriple = (str(x), r.replace('_','-'), str(y))
                
                
                try:
                    amr = Amr.from_triples(amr.triples(instances=False)+[newtriple], amr.node_to_concepts)
                except ValueError as ex:
                    print('Ignoring triple so as to avoid cycle:', ex.message, file=sys.stderr)

                completed[1][(h,i)] = True

    '''
    # simplify adverbs to adjectives based on lexicon
    for v in amr.node_to_concepts.keys():
        amr.node_to_concepts[v] = simplify_adv(amr.node_to_concepts[v])
    '''
    
    return depParse, amr, alignment, completed

