'''
Marks coreferring concepts by linking them with a :-COREF relation.

@author: Nathan Schneider (nschneid)
@since: 2012-08-08
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr

import pipeline
from pipeline import new_concept, loadCoref, choose_head

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    
    coref = loadCoref(sentenceId, ww)
    
    #print(coref)
    
    for cluster in coref.values():
        clusterX = None # choose an arbitrary member of the cluster to decorate with coreferent equivalents, marked :EQ
        for i,j,w in sorted(cluster, key=lambda mention: (mention[1]-mention[0],wTags[mention[1]]["PartOfSpeech"]), reverse=True): 
            # for each mention, starting with longer and alphabetically-later-POS-tagged mentions (to prioritize nouns over pronouns)
            assert ' '.join(filter(None, ww[i:j+1]))==w,(w,i,j, ww[i:j+1])
            h = choose_head(range(i,j+1), depParse)
            x = alignment[:h] # index of variable associated with the head, if any
            if not (x or x==0): # need a new variable
                print('TODO: coreferring mention not yet in AMR')
                assert False,(i,j,w,h,x)
            if clusterX is None:
                clusterX = x
            elif x==clusterX:
                assert False,('coreferent has same head',i,j,w,h,x,clusterX)
            else:
                newtriple = (str(clusterX), '-COREF', str(x))
                try:
                    amr = Amr.from_triples(amr.triples(instances=False)+[newtriple], amr.node_to_concepts)
                except ValueError as ex:
                    print('Ignoring triple so as to avoid cycle:', ex.message, file=sys.stderr)

    return depParse, amr, alignment, completed
