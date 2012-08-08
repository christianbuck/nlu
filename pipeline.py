#!/usr/bin/env python2.7
'''
Driver and utilities for English-to-AMR pipeline.
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

from dev.amr.amr import Amr
from alignment import Alignment

def main(sentenceId):
    # load dependency parse from sentence file
    tokens, ww, wTags, depParse = loadDepParse(sentenceId)
    
    # pipeline steps
    import nes, vprop, nprop, adjsAndAdverbs, auxes, coref, beautify

    # initialize input to first pipeline step
    token_accounted_for = [False]*len(depParse)
    '''Has the token been accounted for yet in the semantics?'''
    
    edge_accounted_for = {(dep['gov_idx'],m): False for m in range(len(depParse)) if depParse[m] for dep in depParse[m]}
    '''Has the dependency edge been accounted for yet in the semantics?'''
    
    completed = token_accounted_for, edge_accounted_for
    
    amr = Amr()
    alignments = Alignment()

    # serially execute pipeline steps
    print(' '.join(filter(None,ww)))
    sys.stdout.flush()
    for m in [nes, vprop, nprop, adjsAndAdverbs, auxes, coref, beautify]:
        print('\n\nSTAGE: ', m.__name__, '...', file=sys.stderr)
        depParse, amr, alignments, completed = m.main(sentenceId, tokens, ww, wTags, depParse, amr, alignments, completed)
        #print(' '.join(ww))
        print(repr(amr), file=sys.stderr)
        print('Completed:',[depParse[i][0]['dep'] for i,v in enumerate(completed[0]) if v and depParse[i]], file=sys.stderr)
        print(alignments, [deps[0]['dep'] for deps in depParse if deps and not completed[0][deps[0]['dep_idx']]], file=sys.stderr)
        print(amr, file=sys.stderr)
    print(' '.join(tokens))

    print('\n\nRemaining edges:')
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            if dep['gov_idx'] is not None and not completed[1][(dep['gov_idx'],dep['dep_idx'])]:
                print((dep['gov']+'-'+str(dep['gov_idx']),dep['rel'],dep['dep']+'-'+str(dep['dep_idx'])))

    # TODO: output

def token2concept(t):
    t = t.replace('$', '-DOLLAR-')
    res =  re.sub(r'[^A-Za-z0-9-]', '', t).lower() or '??'
    if res=='??':
        assert False, t
    return res


def loadBBN(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['bbn_ne']

def loadVProp(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['prop']
    
def loadNProp(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['nom']

def loadDepParse(sentenceId):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        sentJ = json.load(jsonF)
        
        # words
        tokens = sentJ["treebank_sentence"].split() # includes traces
        ww = [None]*len(tokens)
        wTags = [None]*len(tokens)
        for itm in sentJ["words"]:
            ww[itm[1]["idx"]] = itm[0]
            wTags[itm[1]["idx"]] = itm[1]
        
        # dependency parse
        deps = [None]*len(tokens)   # entries that will remain None: dependency root, punctuation, or function word incorporated into a dependecy relation
        deps_concise = sentJ["stanford_dep"]
        for entry in deps_concise:
            i = entry["dep_idx"]
            if deps[i] is None:
                deps[i] = []
            if entry["gov_idx"]==-1:    # root
                entry["gov_idx"] = None
            deps[i].append(entry)  # can be multiple entries for a token, because tokens can have multiple heads
        
        return tokens, ww, wTags, deps  # ww and wTags have None for tokens which are empty elements

def surface2treeToken(offset, ww):
    '''
    Given a token offset in the (tokenized) surface sentence, 
    convert to a tree token offset by accounting for empty elements/traces.
    ''' # TODO: replace with preprocessing of json files
    i = offset
    while i-ww[:i].count(None)<offset:
        i += 1
    return i

def loadCoref(sentenceId, ww):
    jsonFile = 'examples/'+sentenceId+'.json'
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        chains = json.load(jsonF)["coref_chains"]
        coref = {}  # coref chain ID -> set of elements
        for start,end,chainId,w in chains:
            #start = surface2treeToken(start, ww)    # TODO: unnecessary?
            #end = surface2treeToken(end, ww)
            coref.setdefault(chainId,set()).add((start,end,w))
        return coref

def parents(depParseEntry):
    return [dep['dep_idx'] for dep in depParseEntry] if depParseEntry else []

def parent_edges(depParseEntry):
    return [(dep['gov_idx'],dep['dep_idx']) for dep in depParseEntry] if depParseEntry else []

def choose_head(tokenIndices, depParse):
    # restricted version of least common subsumer:
    # assume that for every word in the NE, 
    # all words on the ancestor path up to the NE's head 
    # are also in the NE
    frontier = set(tokenIndices)    # should end up with just 1 (the head)
    for itm in set(frontier):
        assert 0<=itm<len(depParse)
        if not depParse[itm] or all((depitm['gov_idx'] in tokenIndices) for depitm in depParse[itm]):
            frontier.remove(itm)
    
    if not frontier: return None    # TODO: temporary?
    assert len(frontier)==1,(frontier,tokenIndices,depParse[tokenIndices[0]],depParse[tokenIndices[1]])
    return next(iter(frontier))
    

def new_concept(concept, amr, alignment=None, alignedToken=None):
    # new variable
    x = len(amr.node_to_concepts)
    
    amr.node_to_concepts[str(x)] = concept
    
    if alignedToken is not None:
        alignment.link(x, alignedToken)
    
    return x    # variable, as an integer


if __name__=='__main__':
    sentId = sys.argv[1]
    main(sentId)
