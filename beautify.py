'''
Cleans up superficial issues in the AMR, such as deleting unnecessary :-DUMMY relations and 
-FALLBACK concepts and merging coreferential concepts marked with :-COREF.

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
    
    
    # TODO: update alignments. also record AMR triple-to-token alignments?
    
    triples = amr.triples(instances=False)
    coref_triples = [trip for trip in triples if trip[1]=='-COREF']
    replacements = {}
    for coref_trip in coref_triples:
        x, _, (y,) = coref_trip
        
        assert amr.get_concept(x)==amr.get_concept(y) \
            or wTags[alignment[int(y):]]["PartOfSpeech"] in ['PRP','PRP$'] \
            or amr.get_concept(y).endswith('-FALLBACK'), (y,ww[alignment[int(y):]],x,ww[alignment[int(x):]])
        replacements[y] = x
        triples.remove(coref_trip)
    for v0 in replacements:
        del amr.node_to_concepts[v0]
    
    newtriples = []
    for a, r, (b,) in triples:
        if a in replacements:
            a = replacements[a]
        if b in replacements:
            b = replacements[b]
        newtriples.append((a,r,b))
    amr = Amr.from_triples(newtriples, amr.node_to_concepts)
    
    # TODO: delete unnecessary dummies
    
    # delete -FALLBACK decorations
    for k,v in amr.node_to_concepts.items():
        if v.endswith('-FALLBACK'):
            amr.node_to_concepts[k] = v.replace('-FALLBACK', '')
    
    
    # choose user-friendly variable names
    # assumes current variable names are all integer strings
    old2newvars = {}
    newconcepts = {}
    for v,c in amr.node_to_concepts.items():
        v2 = c[0] if c[0].isalpha() else v
        if v2 in newconcepts:    # append numerical suffix if necessary to disambiguate
            assert v2.isalpha()
            v2 += str(sum(1 for k in newconcepts.keys() if k[0]==v2))
        newconcepts[v2] = c
        old2newvars[v] = v2
    amr = Amr.from_triples([(old2newvars.get(x,x), r, (old2newvars.get(y,y),)) for x,r,(y,) in amr.triples(instances=False)], newconcepts)
    
    
    # detect orphans (variables with no triples)
    orphans = {v: True for v in newconcepts}
    for x,r,(y,) in amr.triples(instances=False):
        if r=='-DUMMY': continue
        orphans[x] = False
        if y in orphans:
            orphans[y] = False
    orphans = [v for v in orphans if orphans[v]]
    print(len(orphans),'orphans',orphans, file=sys.stderr)
    
    # ensure a node has a :-DUMMY annotation iff it is an orphan
    amr = Amr.from_triples([(x,r,(y,)) for x,r,(y,) in amr.triples(instances=False) if r!='-DUMMY']+[(o,'-DUMMY','') for o in orphans], newconcepts)
    
    return depParse, amr, alignment, completed
