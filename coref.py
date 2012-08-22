'''
Marks coreferring concepts by linking them with a :-COREF relation.

@author: Nathan Schneider (nschneid)
@since: 2012-08-08
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline, config
from pipeline import new_concept, new_amr_from_old, loadCoref, choose_head

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    
    coref = loadCoref(jsonFile, ww)
    
    #print(coref)
    
    for cluster in coref.values():
        clusterX = None # choose one member of the cluster to decorate with coreferent equivalents, marked :-COREF
        for i,j,w in sorted(cluster, key=lambda mention: (alignment[:mention[1]] is None or '-FALLBACK_PRON' not in amr.node_to_concepts[str(alignment[:mention[1]])],
                                                          alignment[:mention[1]] is None or '-FALLBACK' not in amr.node_to_concepts[str(alignment[:mention[1]])],
                                                          mention[1]-mention[0]), reverse=True):
            # preferences: pronouns (-FALLBACK_PRON) < hallucinated concepts (-FALLBACK) < content words from the sentence
            assert ' '.join(filter(None, ww[i:j+1]))==w,(w,i,j, ww[i:j+1])
            trips = amr.triples(instances=False)
            h = choose_head(range(i,j+1), depParse)
            x = alignment[:h] # index of variable associated with the head, if any
            if not (x or x==0): # need a new variable
                print('TODO: coreferring mention not yet in AMR')
                assert False,(i,j,w,h,x,amr)
            if clusterX is None:
                clusterX = x
            elif x==clusterX:
                assert False,('coreferent has same head',i,j,w,h,x,clusterX)
            else:
                isCopula = False
                # note that previous modules have inserted some :-COREF links for equivalent nodes
                for x2 in [str(clusterX)]+symmetric_neighbors(str(clusterX), '-COREF', amr):
                    for x3 in [str(x)]+symmetric_neighbors(str(x), '-COREF', amr):
                        if x3 in symmetric_neighbors(x2, 'domain', amr):
                            isCopula = True
                            if config.verbose: print('blocked coreference link (probably a copula cxn) between variables:',x,clusterX, file=sys.stderr)
                            break
                    if isCopula: break
                # copula construction - don't merge as coreferent
                if isCopula:
                    continue

                newtriple = (str(clusterX), '-COREF', str(x))
                
                amr = new_amr_from_old(amr, new_triples=[newtriple])

    return depParse, amr, alignment, completed

def symmetric_neighbors(v, link, amr):
    '''Returns variables of all neighboring nodes to 'v' linked to it by an edge of type 'link' in either direction.'''
    return [(x if y==v else y) for x,r,(y,) in amr.triples(instances=False) if v in [x,y] and r==link]
