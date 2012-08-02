'''
Creates AMR fragments for verb propositions (PropBank-style semantic role structures).

@author: Nathan Schneider (nschneid)
@since: 2012-07-31
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

from dev.amr.amr import Amr

import pipeline
from pipeline import choose_head, new_concept, parent_edges

'''
Example input, from wsj_0002.0:

"prop": [
    {
      "inflection": "-----", 
      "basepos": "v", 
      "baseform": "name", 
      "args": [
        [
          "rel", 
          "16:0", 
          16, 
          16, 
          "named"
        ], 
        [
          "ARG1", 
          "17:0", 
          0, 
          14, 
          "Rudolph Agnew , 55 years old and former chairman of Consolidated Gold Fields PLC ,"
        ], 
        [
          "ARG2", 
          "18:2", 
          18, 
          26, 
          "*PRO*-2 a nonexecutive director of this British industrial conglomerate"
        ], 
        [
          "LINK-PCR", 
          "17:0*17:0", 
          null, 
          null, 
          ""
        ]
      ], 
      "roleset": "name.01"
    }
'''





def main(sentenceId, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    triples = set() # to add to the AMR
    
    props = pipeline.loadVProp(sentenceId)
    
    # add all predicates first, so the roleset properly goes into the AMR
    for prop in props:
        baseform, roleset = prop["baseform"], prop["roleset"]
        
        assert prop["args"][0][0]=='rel'
        pred = prop["args"][0]
        assert pred[2]==pred[3] # multiword predicates?
        ph = pred[2]    # predicate head
        px = alignment[:ph]
        if not (px or px==0):
            px = new_concept(pipeline.token2concept(roleset.replace('.','-')), amr, alignment, ph)
            if len(prop["args"])==1 or prop["args"][1][0].startswith('LINK'):
                triples.add((str(px), 'DUMMY', ''))
        completed[0][ph] = True
        
    # now handle arguments
    for prop in props:
        baseform, roleset = prop["baseform"], prop["roleset"]
        
        pred = [arg for arg in prop["args"] if arg[0]=='rel'][0]
        ph = pred[2]    # predicate head
        px = alignment[:ph]
        
        for rel,treenode,i,j,yieldS in prop["args"]:
            if i is None or j is None: continue # TODO: special PropBank cases that need further work
            if rel in ['rel', 'LINK-PCR', 'LINK-SLC']: continue
            assert rel[:3]=='ARG'
            h = choose_head(range(i,j+1), depParse)
            x = alignment[:h] # index of variable associated with i's head, if any
            
            if rel=='ARGM-TMP':
                # see if it looks syntactically like a temporal modifier
                for dep in depParse[h]:
                    if dep['gov_idx']==ph:
                        if dep['rel']=='tmod':
                            rel = 'time'
                        break
                # TODO: possibly also :duration, etc.
            elif rel=='ARGM-LOC':
                rel = 'location'    # TODO: possibly also :direction, :source, :destination. look at preposition?
            
            if not (x or x==0): # need a new variable
                x = new_concept(pipeline.token2concept(depParse[h][0]['dep']),
                                amr, alignment, h)
            triples.add((str(px), rel, str(x)))
            
            completed[0][h] = True

            # if SRL argument link corresponds to a dependency edge, mark that edge as complete
            if (ph,h) in completed[1]:
                completed[1][(ph,h)] = True
                print('completed ',(ph,h))
            if (h,ph) in completed[1]:  # also for reverse direction
                completed[1][(h,ph)] = True
                print('completed ',(ph,h))
    
    print(triples)
    amr = Amr.from_triples(amr.triples(instances=False)+list(triples), amr.node_to_concepts)

    return depParse, amr, alignment, completed
