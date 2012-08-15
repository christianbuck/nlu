'''
Chooses a root for the AMR, flagging it with '-ROOT'.
Heuristic: the shallowest in the dependency parse of the variables aligned to tokens.

@author: Nathan Schneider (nschneid)
@since: 2012-08-14
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput

import pipeline
from pipeline import choose_head, new_concept, new_amr_from_old, get_or_create_concept_from_token as amrget

def main(sentenceId, tokens, ww, wTags, depParse, inAMR, alignment, completed):
    amr = inAMR
    
    h = choose_head([i for v,i in alignment[:]], depParse)
    
    amr.node_to_concepts[str(alignment[:h])] += '-ROOT'

    return depParse, amr, alignment, completed

