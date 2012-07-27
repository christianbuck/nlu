'''
Attaches adjective and adverb modifiers with the :mod relation.

@author: Nathan Schneider (nschneid)
@since: 2012-07-26
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

from dev.amr.amr import Amr

import pipeline

def main(sentenceId, depParse, inAMR, alignment, completed):
    amr = inAMR
    for itm in depParse[1:]:
        i = itm['address']
        if completed[i]: continue
        if itm['rel'] in ['amod', 'advmod']:
            h = depParse[itm['head']]['address'] # i's head
            x = alignment[:h] # index of variable associated with i's head, if any
            if not (x or x==0): # need a new variable
                assert not completed[h]
                x = max(amr.node_to_concepts.keys())+1
                amr.node_to_concepts[x] = pipeline.token2concept(depParse[itm['head']]['word'])
                alignment.link(x, h)
            y = alignment[:i] # modifier variable
            if not (y or y==0): # new variable
                y = max(amr.node_to_concepts.keys())+1
                amr.node_to_concepts[y] = pipeline.token2concept(itm['word'].lower())
                alignment.link(y, i)
            # attach with :mod relation
            newtriple = (x, 'mod', y)
            amr = Amr.from_triples(amr.triples()+[newtriple], amr.node_to_concepts)
            completed[i] = True

    return depParse, amr, alignment, completed

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
