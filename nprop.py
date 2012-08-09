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

#TODO: the example below is buggy
'''
Example input, from wsj_0002.0:

 "nom": [
    {
      "lemma": "chairman", 
      "frame": "01", 
      "args": [
        [
          "ARGM-TMP", 
          "7:0", 
          7, 
          7, 
          "former"
        ], 
        [
          "ARG0", 
          "8:0", 
          8, 
          8, 
          "chairman"
        ], 
        [
          "rel", 
          "8:0", 
          8, 
          8, 
          "chairman"
        ], 
        [
          "ARG2", 
          "9:1", 
          9, 
          13, 
          "of Consolidated Gold Fields PLC"
        ]
      ], 
      "tokenNr": "8"
    }, 
    {
      "lemma": "conglomerate", 
      "frame": "01", 
      "args": [
        [
          "ARGM-LOC", 
          "23:0", 
          23, 
          23, 
          "this"
        ], 
        [
          "ARG1", 
          "24:0", 
          24, 
          24, 
          "British"
        ], 
        [
          "rel", 
          "25:0", 
          25, 
          25, 
          "industrial"
        ]
      ], 
      "tokenNr": "25"
    }, 
    {
      "lemma": "director", 
      "frame": "01", 
      "args": [
        [
          "ARG3", 
          "19:0", 
          19, 
          19, 
          "a"
        ], 
        [
          "ARG0", 
          "20:0", 
          20, 
          20, 
          "nonexecutive"
        ], 
        [
          "rel", 
          "20:0", 
          20, 
          20, 
          "nonexecutive"
        ], 
        [
          "ARG2", 
          "21:1", 
          19, 
          21, 
          "a nonexecutive director"
        ]
      ], 
      "tokenNr": "20"
    }
'''





def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    triples = set() # to add to the AMR
    
    props = pipeline.loadNProp(sentenceId)
    
    predheads = {}  # map head index to nominal predicate variable (not reflected in the alignment)
    
    # add all predicates first, so the roleset properly goes into the AMR
    for prop in props:
        baseform, frame = prop.get("lemma",prop.get("baseform")), prop["frame"]
        
        preds = {tuple(arg) for arg in prop["args"] if arg[0]=='rel'}
        assert len(preds)==1
        pred = next(iter(preds))
        assert pred[2]==pred[3] # multiword predicates?
        ph = pred[2]    # predicate head
        #px = alignment[:ph]    # instead of aligning noun predicate to noun in the sentence, introduce the noun predicate separately (so the plain noun concept can be its argument)
        px = predheads.get(ph)
        predconcept = pipeline.token2concept(frame.replace('.','-n-'))
        if not (px or px==0):
            px = new_concept(predconcept, amr)  # no alignment here - instead use 'predheads'
            #print('###','newconcept',px,'/',predconcept)
            px0 = alignment[:ph]
            if not (px0 or px0==0):
                px0 = new_concept(pipeline.token2concept(ww[ph]), amr, alignment, ph)
            triples.add((str(px), '-PRED-FOR', str(px0)))
            #if len(prop["args"])==1 or (prop["args"][0][0] in ['Support','rel'] and prop["args"][1][0] in ['Support','rel']):
            #    triples.add((str(px), '-DUMMY', ''))
            predheads[ph] = px
        #else:   # predicate already a concept in the AMR
        #    amr.node_to_concepts[str(px)] = predconcept # change the name of the concept
        
        completed[0][ph] = True
        
    # now handle arguments
    for prop in props:
        baseform, frame = prop["baseform"], prop["frame"]
        
        pred = [arg for arg in prop["args"] if arg[0]=='rel'][0]
        ph = pred[2]    # predicate head
        #px = alignment[:ph]
        px = predheads[ph]
        
        for rel,treenode,i,j,yieldS in prop["args"]:
            if i is None or j is None: continue # TODO: special PropBank cases that need further work
            if rel in ['rel', 'Support']: continue
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
            elif rel=='ARGM-CAU':
                rel = 'cause'
            
            if not (x or x==0): # need a new variable
                x = new_concept(pipeline.token2concept(ww[h]),
                                amr, alignment, h)
            triples.add((str(px), rel, str(x)))
            print('###',px,rel,x)
            
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
