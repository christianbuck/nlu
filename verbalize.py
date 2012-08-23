'''
Attempt to verbalize things where possible - currently noun propositions 
to known associated verb propositions (based on a list extracted from NomBank).

@author: Nathan Schneider (nschneid)
@since: 2012-08-09
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept, new_amr, new_amr_from_old

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    triples = amr.triples(instances=False)
    
    # find noun propositions in the AMR. extract edges of the form (x / xword :-PRED (y / lemma-n.01))
    npropedges = [trip for trip in triples if trip[1]=='-PRED']
    for x,r,(y,) in npropedges:
        npred = amr.get_concept(y)
        nlemma, nsense = re.match(r'^(.+)-n-(\d\d|XX)$', npred).groups()
        npred = nlemma+'.'+nsense
        # get corresponding verb, vpred
        vpred = nompred2verbpred(npred)
        
        if vpred:
            vlemma, vsense = re.match(r'^verb-(.+)\.(\d\d|XX)$', vpred).groups()
            vpred = vlemma+'-'+vsense
            
            # check whether there is a self-reference (~ incorporated argument)
            selfrefs = {r2 for y2,r2,(x2,) in triples if x2==x and y2==y}
            if selfrefs:
                assert len(selfrefs)==1,selfrefs
                r2 = next(iter(selfrefs))
                # new configuration: (x / thing-FALLBACK :ARG#-of (y / vlemma.01))
                # i.e. rename the x and y concepts and the relation between them
                # do not change the alignments (x continues to be aligned to a token, 
                # y continues to be unaligned)
                triples.append((x,r2+'-of',(y,)))
                amr.node_to_concepts[x] = 'thing-FALLBACK'
                amr.node_to_concepts[y] = vpred
            else:
                # probably an eventive noun, so we will not need the predicate 
                # to be a separate concept. for now, mark the two nodes as coreferential 
                # and label them both with the verbal predicate.
                triples.append((x,'-COREF',(y,)))
                amr.node_to_concepts[x] = amr.node_to_concepts[y] = vpred
        else:   # for now, just keep the nominal predicate (copy it from y to x and mark them as coreferent)
            triples.append((x,'-COREF',(y,)))
            amr.node_to_concepts[x] = amr.node_to_concepts[y]
        triples.remove((x,r,(y,)))
    
        amr = new_amr(triples, amr.node_to_concepts)
        
    return depParse, amr, alignment, completed

_npred2vpred = {}
def nompred2verbpred(nompred):
    '''
    >>> nompred2verbpred('gift.01')
    'verb-give.01'
    >>> nompred2verbpred('destruction.01')
    'verb-destroy.01'
    >>> nompred2verbpred('institution.01')
    '''
    global _npred2vpred
    if not _npred2vpred:
        with open('nombank-deverbals-combined.txt') as inF:
            for ln in inF:
                npred, vpred, arg = ln[:-1].split('\t')
                if npred in _npred2vpred:
                    assert _npred2vpred[npred]==vpred
                else:
                    _npred2vpred[npred] = vpred
    return _npred2vpred.get(nompred)

if __name__=='__main__':
    import doctest
    doctest.testmod()

