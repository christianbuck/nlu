'''
Cleans up superficial issues in the AMR, such as deleting unnecessary :-DUMMY relations 
and merging coreferential concepts marked with :-COREF.

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
    
    # for each triple of the form <x :-COREF y>, delete the triple and replace 
    # all occurrences of y with x
    
    triples = amr.triples(instances=False)
    coref_triples = [trip for trip in triples if trip[1]=='-COREF']
    replacements = {}
    for coref_trip in coref_triples:
        x, _, (y,) = coref_trip
        assert wTags[alignment[int(y):]]["PartOfSpeech"] in ['PRP','PRP$'], (y,ww[alignment[int(y):]],x,ww[alignment[int(x):]])
        replacements[y] = x
        triples.remove(coref_trip)
    
    newtriples = []
    for a, r, (b,) in triples:
        if a in replacements:
            a = replacements[a]
        if b==y:
            b = replacements[b]
        newtriples.append((a,r,b))
    amr = Amr.from_triples(newtriples, amr.node_to_concepts)
    
    # TODO: delete unnecessary dummies
    
    return depParse, amr, alignment, completed
