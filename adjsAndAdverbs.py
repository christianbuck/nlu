'''
Attaches adjective and adverb modifiers with the :mod relation.

@author: Nathan Schneider (nschneid)
@since: 2012-07-26
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import new_concept_from_token, new_amr_from_old

def main(sentenceId, jsonFile, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    for deps in depParse:
        if deps is None: continue
        for itm in deps:
            if completed[1][(itm['gov_idx'],itm['dep_idx'])]: continue
            i = itm['dep_idx']
            if itm['rel'] in ['amod', 'advmod', 'dep', 'num', 'number', 'det']:
                h = itm['gov_idx'] # i's head
                
                if itm['rel']=='det' and itm['dep'].lower() in ['the', 'a', 'an']:
                    # skip articles
                    completed[0][i] = True
                    completed[1][(h,i)] = True
                    continue
                
                x = alignment[:h] # index of variable associated with i's head, if any
                if not (x or x==0): # need a new variable
                    assert not completed[0][h], (depParse[h],amr)
                    x = new_concept_from_token(amr, alignment, h, depParse, wTags)
                    completed[0][h] = True
                y = alignment[:i] # modifier variable
                if not (y or y==0): # new variable
                    y = new_concept_from_token( amr, alignment, i, depParse, wTags)
                    completed[0][i] = True
                if itm['rel'] in ['num', 'number']:   # attach as :quant
                    newtriple = (str(x), 'quant', str(y))   # TODO: for plain values, don't create a variable
                elif 'AGE' in amr.get_concept(str(y)).split('-'):
                    newtriple = (str(x), 'age', str(y))
                    amr.node_to_concepts[str(y)] = amr.node_to_concepts[str(y)].replace('-AGE','')
                else:   # attach with :mod relation
                    newtriple = (str(x), 'mod', str(y))
                
                
                amr = new_amr_from_old(amr, new_triples=[newtriple])
                
                completed[1][(h,i)] = True

    # simplify adverbs to adjectives based on lexicon
    for v in amr.node_to_concepts.keys():
        amr.node_to_concepts[v] = simplify_adv(amr.node_to_concepts[v])

    return depParse, amr, alignment, completed

adv_adj_lex = None
def simplify_adv(w):
    '''Try to simplify an adverb given a lexicon of corresponding adjectives.
    E.g. seriously -> serious. If not found in the lexicon, return the input.'''
    global adv_adj_lex
    if adv_adj_lex is None:
        adv_adj_lex = {}
        with codecs.open('adj-adv-pairs.txt', 'r', 'utf-8') as lexF:
            for ln in lexF:
                adj, adv = ln[:-1].split('\t')
                if adv not in adv_adj_lex or len(adv_adj_lex[adv])>len(adj):
                    adv_adj_lex[adv] = adj
    return adv_adj_lex.get(w,w)

def sample_dep_parse():
    from nltk.corpus import dependency_treebank
    p = dependency_treebank.parsed_sents()[0]
    
    ''' with 'rel' from Stanford dependencies:
    [{'address': 0, 'deps': [8], 'rel': 'TOP',           'tag': 'TOP', 'word': None},
     {'address': 1, 'deps': [],  'rel': 'nn', 'head': 2, 'tag': 'NNP', 'word': Pierre},
      ...]
    '''

    '''
    Stanford dependencies
    Collapsed dependencies with CC processed

    nn ( Vinken-2 , Pierre-1 )
    nsubj ( join-9 , Vinken-2 )
    num ( years-5 , 61-4 )
    npadvmod ( old-6 , years-5 )
    amod ( Vinken-2 , old-6 )
    aux ( join-9 , will-8 )
    det ( board-11 , the-10 )
    dobj ( join-9 , board-11 )
    det ( director-15 , a-13 )
    amod ( director-15 , nonexecutive-14 )
    prep_as ( join-9 , director-15 )
    tmod ( join-9 , Nov.-16 )
    num ( Nov.-16 , 29-17 ) 
    '''
