'''
Attaches adjective and adverb modifiers with the :mod relation.

@author: Nathan Schneider (nschneid)
@since: 2012-08-02
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr

import pipeline
from pipeline import new_concept

MODALS = {'will': '', 
          'must': 'obligate-01', 
          'may': 'possible-OR-permit-01',
          'might': 'possible', 
          'can': 'possible-OR-permit-01',
          'could': 'possible-OR-permit-01', 
          'should': 'recommend-01',
          'shall': 'obligate-01'}  # modal auxiliaries

# TODO: other modalities not expressed exclusively in the auxiliary: e.g. 'would rather', 'likely/able/permitted/have to'

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    for deps in depParse:
        if deps is None: continue
        for itm in deps:
            if completed[1][(itm['gov_idx'],itm['dep_idx'])]: continue
            i = itm['dep_idx']
            if itm['rel'] in ['aux', 'auxpass']:
                if wTags[i]["PartOfSpeech"]!='MD':
                    # BE or HAVE auxiliary--ignore
                    completed[0][i] = True
                    completed[1][(itm['gov_idx'],i)] = True
                    continue
                
                assert False,'TODO'
                
                h = itm['gov_idx'] # i's head
                x = alignment[:h] # index of variable associated with i's head, if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][h]
                    w = depParse[itm['gov_idx']][0]['dep']  # modifier token
                    x = new_concept(pipeline.token2concept(w), amr, alignment, h)
                    completed[0][h] = True
                y = alignment[:i] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept(pipeline.token2concept(itm['dep'].lower()), amr, alignment, i)
                    completed[0][i] = True
                
                newtriple = (None,) # TODO
                
                amr = Amr.from_triples(amr.triples(instances=False)+[newtriple], amr.node_to_concepts)

                completed[1][(itm['gov_idx'],i)] = True

    return depParse, amr, alignment, completed
