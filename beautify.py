'''
Cleans up superficial issues in the AMR, such as deleting unnecessary :-DUMMY relations and 
-FALLBACK concepts and merging coreferential concepts marked with :-COREF.

@author: Nathan Schneider (nschneid)
@since: 2012-08-08
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline, config
from pipeline import new_concept, new_amr, new_amr_from_old, loadCoref, choose_head
from alignment import Alignment

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    
    
    # clean up role names: :mod-nn and :MOD => :mod
    repltriples = [(x, r, (y,)) for x,r,(y,) in amr.triples(instances=False) if r in ['mod-NN','MOD']]
    newtriples = [(x, 'mod', (y,)) for x,r,(y,) in repltriples]
    amr = new_amr_from_old(amr, new_triples=newtriples, avoid_triples=repltriples)
    
    
    
    
    # for each triple of the form <x :-COREF y>, delete the triple and replace 
    # all occurrences of y with x
    
    
    
    triples = amr.triples(instances=False)
    
    # Use -COREF flags to establish a mapping from current to new variables 
    
    coref_triples = [trip for trip in triples if trip[1]=='-COREF']
    replacements = {}
    for coref_trip in coref_triples:
        x, _, (y,) = coref_trip
        
        assert amr.get_concept(x).replace('-ROOT','')==amr.get_concept(y).replace('-ROOT','') \
            or (alignment[int(y):] is not None and wTags[alignment[int(y):]]["PartOfSpeech"] in ['PRP','PRP$']) \
            or amr.get_concept(y).endswith('-FALLBACK'), (y,ww[alignment[int(y):]],x,ww[alignment[int(x):]])
        replacements[y] = x
    
    # MERGE the coreferent nodes
    
    all_triples = []
    trip2tokAlignment = Alignment('many2one') # source side indexes 'all_triples'
    
    newtriples = []
    oldtriples = coref_triples
    for a, r, (b,) in triples:
        if r=='-COREF': continue
        trip = (a,r,(b,))
        
        change = False
        if a in replacements:
            a = replacements[a]
            change = True
        if b in replacements:
            b = replacements[b]
            change = True
        if change:
            newtriples.append((a,r,b))
            oldtriples.append(trip)
            
        if isinstance(b,basestring) and b in amr.node_to_concepts and alignment[int(b):] is not None:
            trip2tokAlignment.link(len(all_triples), alignment[int(b):])
        all_triples.append((a,r,b))
        
        
    amr = new_amr_from_old(amr, new_triples=newtriples, avoid_triples=oldtriples, avoid_concepts=replacements)
    
    
    # delete -FALLBACK decorations
    for k,v in amr.node_to_concepts.items():
        if v.endswith('-FALLBACK'):
            amr.node_to_concepts[k] = v.replace('-FALLBACK', '')
    
    if config.verbose:
        print('Triple-to-token alignment:',{trip:ww[trip2tokAlignment[t:]]+'-'+str(trip2tokAlignment[t:]) for t,trip in enumerate(all_triples) if trip2tokAlignment[t:] is not None},
              file=sys.stderr)
    
    
    
    
    
    # delete CARDINAL concepts (cf. the nes module) unless the concept has no parent
    # e.g. in wsj_0077.14, "154.2 million shares" is converted from (s / shares :quant (c / CARDINAL :quant 154200000)) to (s / shares :quant 154200000)
    cardinals = {v for v,c in amr.node_to_concepts.items() if c=='CARDINAL'}
    for v in cardinals:
        old2newvars = {}
        triples = [(x,r,y) for x,r,(y,) in amr.triples(instances=False) if x==v or y==v]
        try:
            assert 1<=len(triples)<=2,(triples,amr)
        except AssertionError:  # something complicated; just punt
            continue
        if len(triples)<2: continue
        t1, t2 = triples
        if t1[2]!=v:
            t1, t2 = t2, t1
        assert t1[2]==t2[0]==v
        old2newvars[v] = t2[2]
        del amr.node_to_concepts[v]
        
        newtrip = (t1[0],t1[1],t2[2])
        assert newtrip[0]!=newtrip[2]
        # replace t1 and t2 with newtrip
        amr = new_amr_from_old(amr, new_triples=[newtrip], avoid_triples=[t1,t2])
        if config.verbose: print('merge CARDINAL:',[t1,t2],'->',newtrip, file=sys.stderr)
        
        t = all_triples.index(t1)
        #assert trip2tokAlignment[t:] is not None
        all_triples[t] = newtrip
        #assert trip2tokAlignment[all_triples.index(t2):] is None
        
        #amr = new_amr([(old2newvars.get(x,x), r, (old2newvars.get(y,y),)) for x,r,(y,) in amr.triples(instances=False) if x!=v], amr.node_to_concepts)
    
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
    all_triples2 = []
    trip2tokAlignment2 = Alignment('many2one')
    for x,r,(y,) in amr.triples(instances=False):
        t = all_triples.index((x,r,y))
        if trip2tokAlignment[t:] is not None:
            trip2tokAlignment2.link(len(all_triples2), trip2tokAlignment[t:])
        all_triples2.append((old2newvars.get(x,x), r, (old2newvars.get(y,y),)))
    
    finalAlignment = {trip:ww[trip2tokAlignment2[t:]]+'-'+str(trip2tokAlignment2[t:]) for t,trip in enumerate(all_triples2) if trip2tokAlignment2[t:] is not None}
    if config.verbose:
        print('Final triple-to-token alignment:',finalAlignment,
              file=sys.stderr)
    
    amr = new_amr(all_triples2, newconcepts)
    
    
    # detect orphans (variables with no triples)
    orphans = {v: True for v in newconcepts}
    for x,r,(y,) in amr.triples(instances=False):
        if r=='-DUMMY': continue
        orphans[x] = False
        if y in orphans:
            orphans[y] = False
    orphans = [v for v in orphans if orphans[v]]
    if config.verbose: print(len(orphans),'orphans',orphans, file=sys.stderr)
    
    # ensure a node has a :-DUMMY annotation iff it is an orphan
    amr = new_amr([(x,r,(y,)) for x,r,(y,) in amr.triples(instances=False) if r!='-DUMMY']+[(o,'-DUMMY','') for o in orphans], newconcepts)
    
    
    def swap_callback((x,r,(y,)),(x2,r2,(y2,))):
        #TODO: fix alignments
        pass
    
    # Make the concept with -ROOT the root, inverting edges as necessary.
    roots = [v for v,cname in amr.node_to_concepts.items() if '-ROOT' in cname]
    assert len(roots)==1,('Need a unique root',amr.node_to_concepts)
    root = roots[0]
    if not amr.is_connected():
        print('<<<<AMR is not connected!','for Amr.from_triples(',amr.triples(instances=False),',',amr.node_to_concepts,')', file=sys.stdout)
    else:
        print('<<<<calling make_rooted_amr with',root,'for Amr.from_triples(',amr.triples(instances=False),',',amr.node_to_concepts,')', file=sys.stdout)
        #amr = amr.make_rooted_amr(root, swap_callback)
    
    return depParse, amr, finalAlignment, completed
