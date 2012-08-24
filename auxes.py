'''
Attaches adjective and adverb modifiers with the :mod relation.

@author: Nathan Schneider (nschneid)
@since: 2012-08-02
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept_from_token, new_amr_from_old

MODALS = {'will': '', 
          'would': '',
          'must': 'obligate-01', 
          'may': 'possible-OR-permit-01',
          'might': 'possible', 
          'can': 'possible-OR-permit-01',
          'could': 'possible-OR-permit-01', 
          'should': 'recommend-01',
          'shall': 'obligate-01'}  # modal auxiliaries

# TODO: used-to = use-03

ACTION_ARG = {'obligate-01': 'ARG2', 'permit-01': 'ARG1', 'possible': 'domain', 'recommend-01': 'ARG1',
              'possible-OR-permit-01': 'domain'}

# TODO: other modalities not expressed exclusively in the auxiliary: e.g. 'would rather', 'likely/able/permitted/have to'

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
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
                
                #print(itm, file=sys.stderr)
                
                mw = itm["dep"]
                mpred = MODALS[mw]
                
                
                x = alignment[:i] # index of variable associated with i's head, if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][i]
                    x = new_concept_from_token(amr, alignment, i, depParse, wTags, concept=pipeline.token2concept(mpred))
                    completed[0][i] = True
                    
                h = itm["gov_idx"] # i's head
                y = alignment[:h] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept_from_token(amr, alignment, h, depParse, wTags)
                    completed[0][h] = True
                
                newtriple = (str(x), ACTION_ARG[mpred], str(y))

                amr = new_amr_from_old(amr, new_triples=[newtriple])

                completed[1][(itm['gov_idx'],i)] = True

    return depParse, amr, alignment, completed
