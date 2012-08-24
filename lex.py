'''
Loads and queries a morphological lexicon. So far, just a stemmer for nouns.

Requires EnglMorphFullCache.txt (20M, thus not included in version control).

@deprecated: Since we have lemmas from the Stanford tagger, it's easier to 
use those instead.

@author: Nathan Schneider (nschneid)
@since: 2012-08-23
'''
from __future__ import print_function
import re, sys, os

_w2stem = {}
def stem_noun(w, verbose=False):
    '''
    Returns the stem for the given noun according to the lexicon. 
    The result will be None if the stem is not found, is not listed as a noun or proper name, 
    or does not differ from the form provided.
    
    >>> stem_noun('given')
    >>> stem_noun('were')
    >>> stem_noun('hospitalizations')
    'hospitalization'
    >>> stem_noun('foci')
    'focus'
    >>> stem_noun('illuminati')
    >>> stem_noun('Hittites')
    'Hittite'
    >>> stem_noun('Guyana dollars')
    'Guyana dollar'
    >>> stem_noun('data')
    '''
    global _w2stem
    if not _w2stem:
        pastHeader = False
        with open('EnglMorphFullCache.txt') as inF:
            if verbose: print('Loading English morphology cache...', file=sys.stderr)
            for ln in inF:  # e.g. ::SURF "Acanthoscelides obtectuses" ::LEX "Acanthoscelides obtectus" ...
                if not pastHeader:
                    if ln[0]=='#': continue
                    else:
                        pastHeader = True
                m = re.search(r'::SURF "(.+?)" .*::LEX "(.+?)" .*::SYNT [A-Z-]+-(?:NOUN|NAME)', ln[:-1])
                if not m: continue  # e.g., non-nouns
                surface, stem = m.groups()
                #_w2stem.setdefault(surface, set()).add(stem)
                if surface.lower()==stem.lower(): continue  # if only a case difference (e.g. acronyms), don't store it
                
                if surface in _w2stem and _w2stem[surface].lower()!=stem.lower():
                    if len(_w2stem[surface])<len(stem):
                        _w2stem[surface] = stem # keep the longer one if they differ in length; otherwise keep the first one
                    if verbose: print('  Multiple possible stems:',(surface,stem),(surface,_w2stem[surface]), file=sys.stderr)
                    # most of the conflicts are due to spelling variants, esp. with -y vs. -ie (caddy, caddie)
                else:
                    _w2stem[surface] = stem
            if verbose: print('Done loading English morphology cache.', file=sys.stderr)
                
    return _w2stem.get(w)

if __name__=='__main__':
    import doctest
    doctest.testmod()
