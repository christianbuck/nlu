'''
Creates AMR fragments for named entities.

@author: Nathan Schneider (nschneid)
@since: 2012-07-30
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

from dev.amr.amr import Amr

import pipeline
from pipeline import choose_head, new_concept, parent_edges

'''
Example input, from wsj_0002.1:

bbn_ne: { [
      0, 
      1, 
      "Rudolph Agnew", 
      "PERSON", 
      "", 
      "chairman", 
      false
    ], ...,

    [
      10, 
      13, 
      "Consolidated Gold Fields PLC", 
      "ORGANIZATION", 
      "CORPORATION", 
      "", 
      false
    ], ...}
'''





def main(sentenceId, depParse, inAMR, alignment, completed):
    amr = inAMR
    triples = set() # to add to the AMR
    
    entities = pipeline.loadBBN(sentenceId)
    for i,j,name,coarse,fine,desc,_ in entities:    # TODO: what is the last one?
        h = choose_head(range(i,j+1), depParse)
        #print((i,j),name,h,depParse[h+1]['dep'], file=sys.stderr)
        # TODO: if descriptor is present, get its index
        
        x = alignment[:h] # index of variable associated with i's head, if any
        
        if coarse.endswith('_DESC'):
            assert j==i
            # make the word the AMR head
            if not (x or x==0): # need a new variable
                x = new_concept(pipeline.token2concept(depParse[h+1][0]['dep']), amr, alignment, h)
                triples.add((str(x), 'DUMMY', ''))
        else:
            if not (x or x==0): # need a new variable
                x = new_concept(pipeline.token2concept(desc or fine.lower().replace('other','') or coarse.lower()),
                                amr, alignment, h)
                # TODO: also align to descriptor, if present
                n = new_concept('name', amr)
                triples.add((str(x), 'name', str(n)))
                for iw,w in enumerate(name.split()):
                    triples.add((str(n), 'op'+str(iw+1), '"'+w+'"'))
                    
        
        for k in range(i,j+1):
            assert not completed[0][k]
            completed[0][k] = True
            print('completed token',k)
            if k!=h:
                for link in parent_edges(depParse[k]):
                    completed[1][link] = True  # we don't need to attach non-head parts of names anywhere else
    
    amr = Amr.from_triples(amr.triples(instances=False)+list(triples), amr.node_to_concepts)

    return depParse, amr, alignment, completed
