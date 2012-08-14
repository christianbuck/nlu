#coding=UTF-8
'''
Creates AMR fragments for named entities.

@author: Nathan Schneider (nschneid)
@since: 2012-07-30
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json

import pipeline
from pipeline import choose_head, new_concept, new_amr_from_old, parent_edges

'''
Example input, from wsj_0002.0:

"bbn_ne": { [
      0, 
      1, 
      "Rudolph Agnew", 
      "PERSON", 
      "", 
      "chairman", 
      false
    ], ...,

    [
      10, 
      13, 
      "Consolidated Gold Fields PLC", 
      "ORGANIZATION", 
      "CORPORATION", 
      "", 
      false
    ], ...}
'''





def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    triples = set() # to add to the AMR
    
    entities = pipeline.loadBBN(sentenceId)
    for i,j,name,coarse,fine,raw in entities:    # TODO: what is the last one?
        
        if raw.startswith('<TIMEX'): continue  # TODO: NUMEX, TIMEX
        
        h = choose_head(range(i,j+1), depParse)
        #print((i,j),name,h,depParse[h+1]['dep'], file=sys.stderr)
        
        x = alignment[:h] # index of variable associated with i's head, if any
        
        if raw.startswith('<NUMEX'):
            if coarse in ['MONEY','CARDINAL','PERCENT']:
                # get normalized value from Stanford tools
                v = wTags[h]["NormalizedNamedEntityTag"]
                
                wrapper = None
                if v[0] in '<>':
                    if len(v)==1:
                        print('Warning: Unexpected NormalizedNamedEntityTag:',v,'for',raw, file=sys.stderr)
                    else:
                        if v[1]=='=':
                            reln = v[:2]
                            v = v[2:]
                        else:
                            reln = v[0]
                            v = v[1:]
                        concept = {'<': 'less-than', '>': 'more-than', '<=': 'no-more-than', '>=': 'at-least'}[reln]
                        wrapper = new_concept(concept, amr, alignment, h)
                    
                if coarse=='MONEY':
                    m = re.match(r'^([\$¥£])(\d+\.\d+(E-?\d+)?)$', v)
                    if not m:
                        assert False,v
                    u = m.group(1)
                    v = m.group(2)
                elif coarse=='PERCENT':
                    m = re.match(r'^%(\d+\.\d+(E-?\d+)?)$', v)
                    if not m:
                        assert False,v
                    v = m.group(1)
                
                try:
                    v = float(v)
                    if str(v).endswith('.0'):
                        v = int(v)
                except ValueError:
                    pass
                
                if (wrapper is None or coarse=='MONEY') and not (x or x==0): # need a new variable
                    _args = [{'MONEY': 'monetary-quantity', 'PERCENT': 'percentage-entity'}.get(coarse, coarse.upper()), amr]
                    if wrapper is None: # if there is a wrapper concept (e.g. 'more-than'), it is aligned, so don't provide an alignment for x
                        _args += [alignment, h]
                    x = new_concept(*_args)
                
                if (x or x==0):
                    triples.add((str(x), 'value' if coarse=='PERCENT' else 'quant', v))
                    if wrapper is not None:
                        triples.add((str(wrapper), 'op1', str(x)))
                elif wrapper is not None:
                        triples.add((str(wrapper), 'op1', v))   # e.g. more-than :op1 41
                
                
                if coarse=='MONEY':
                    y = new_concept({'$': 'dollar', '¥': 'yen', '£': 'pound'}[u.encode('utf-8')], amr)
                    triples.add((str(x), 'unit', str(y)))
            else:
                assert False,(i,j,raw)
        elif coarse.endswith('_DESC'):
            # make the phrase head word the AMR head concept
            # (could be a multiword term, like Trade Representative)
            if not (x or x==0): # need a new variable
                x = new_concept(pipeline.token2concept(depParse[h][0]['dep']), amr, alignment, h)
                triples.add((str(x), '-DUMMY', '')) # ensure the concept participates in some triple so it is printed
        else:
            if not (x or x==0): # need a new variable
                ne_class = fine.lower().replace('other','') or coarse.lower()
                concept, amr_name = amrify(ne_class, name)
                x = new_concept(pipeline.token2concept(concept)+'-FALLBACK',    # -FALLBACK indicates extra information not in the sentence (NE class)
                                amr, alignment, h)
                n = new_concept('name', amr)
                triples.add((str(x), 'name', str(n)))
                for iw,w in enumerate(amr_name.split()):
                    triples.add((str(n), 'op'+str(iw+1), '"'+w+'"'))
                    
        
        for k in range(i,j+1):
            assert not completed[0][k]
            completed[0][k] = True
            #print('completed token',k)
            if k!=h:
                for link in parent_edges(depParse[k]):
                    completed[1][link] = True  # we don't need to attach non-head parts of names anywhere else
    
    amr = new_amr_from_old(amr, new_triples=list(triples))

    return depParse, amr, alignment, completed

# TODO: incorporate Mr., Mrs., etc. in the name
# TODO: Dr. -> doctor

# TODO: find a real list of nationalities -> country names
NATIONALITIES = {'Chinese': 'China', 'Balinese': 'Bali', 'French': 'France', 'Dutch': 'Netherlands', 
                 'Irish': 'Ireland', 'Scottish': 'Scotland', 'Welsh': 'Wales', 'English': 'England', 'British': 'Britain', 
                 'Finnish': 'Finland', 'Swedish': 'Sweden', 'Spanish': 'Spain',
                 'Somali': 'Somalia', 'Hawaiian': 'Hawaii', 'Brazilian': 'Brazil', 
                 'Kentuckian': 'Kentucky', 'Italian': 'Italy', 'German': 'Germany', 'Norwegian': 'Norway', 
                 'Belgian': 'Belgium', 'Washingtonian': 'Washington', 'Canadian': 'Canada'}
def amrify(ne_class, name):
    concept = ne_class
    if ne_class=='corporation':
        concept = 'company'
    elif ne_class=='nationality':
        concept = 'country'
        if name in NATIONALITIES:
            name = NATIONALITIES[name]
        else:
            name = re.sub(r'i$', '', name)  # Iraqi -> Iraq
            name = re.sub(r'ian$', 'ia', name)   # Russian -> Russia, Australian -> Australia, Indian -> India
            name = re.sub(r'([aeiouy])an$', r'\1', name) # Tennesseean -> Tennessee, New Jerseyan -> New Jersey
            name = re.sub(r'an$', 'a', name)    # Moldovan -> Moldova, Sri Lankan -> Sri Lanka, Rwandan -> Rwanda, American -> America
            name = re.sub(r'ese$', '', name)    # Japanese -> Japan
        
    return concept, name
    
