#!/usr/bin/env python2.7
'''
Driver and utilities for English-to-AMR pipeline.
'''
from __future__ import print_function
import os, sys, re, codecs, fileinput, json, glob, time, traceback

from collections import defaultdict

import config

from dev.amr.amr import Amr
from alignment import Alignment
from add_prop import SpanTree, span_from_treepos

def main(files):
    # pipeline steps
    import nes, timex, conjunctions, vprop, nprop, verbalize, copulas, adjsAndAdverbs, auxes, misc, coref, top, beautify
    # TODO: does conjunctions module work gracefully when propositions are conjoined?
    
    nSents = len(files)
    nSuccess = nConnected = 0
    iSent = 0
    
    for f in files:

        try:
            sentenceId = os.path.basename(f).replace('.json','')
            print(sentenceId)
        
            # load dependency parse from sentence file
            tokens, ww, wTags, depParse = loadDepParse(f)

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
            print()
            sys.stdout.flush()


            for m in [nes, timex, conjunctions, vprop, nprop, verbalize, copulas, adjsAndAdverbs, auxes, misc, coref, top, beautify]:
                if config.verbose:
                    print('\n\nSTAGE: ', m.__name__, '...', file=sys.stderr)
                depParse, amr, alignments, completed = m.main(sentenceId, f, tokens, ww, wTags, depParse, amr, alignments, completed)
                #print(' '.join(ww))
                if config.verbose:
                    print(repr(amr), file=sys.stderr)
                    print('Completed:',[depParse[i][0]['dep'] for i,v in enumerate(completed[0]) if v and depParse[i]], file=sys.stderr)
                    print(alignments, [deps[0]['dep'] for deps in depParse if deps and not completed[0][deps[0]['dep_idx']]], file=sys.stderr)
                    print(amr, file=sys.stderr)
                
            if config.verbose:
                print(' '.join(tokens), file=sys.stderr)
        
            print(amr)
            #amr.render()
            #print('Amr.from_triples(',amr.triples(instances=False),',',amr.node_to_concepts,')')
            print()
            if config.alignments:
                print(alignments)
                print()
    
            if config.verbose:
                print('\n\nRemaining edges:', file=sys.stderr)
                for deps in depParse:
                    if deps is None: continue
                    for dep in deps:
                        if dep['gov_idx'] is not None and not completed[1][(dep['gov_idx'],dep['dep_idx'])]:
                            print((dep['gov']+'-'+str(dep['gov_idx']),dep['rel'],dep['dep']+'-'+str(dep['dep_idx'])), file=sys.stderr)


            nSuccess += 1
            if amr.is_connected(warn=None):
                nConnected += 1
            
        except Exception as ex:
            if not config.errorTolerant:
                raise
            print(sentenceId, file=sys.stderr)
            traceback.print_exception(*sys.exc_info())
            time.sleep(0)
            
        iSent += 1
        print('{}/{}, {} succeeded ({} connected)'.format(iSent, nSents, nSuccess, nConnected), file=sys.stderr)

def token2concept(t):
    t = t.replace('$', '-DOLLAR-')
    res =  re.sub(r'[^A-Za-z0-9-]', '', t).lower() or '??'
    if res=='??':
        assert False, t
    return res


def loadBBN(jsonFile):
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['bbn_ne']

def loadVProp(jsonFile):
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        data = json.load(jsonF)
        props = [prop for prop in data["prop"] if prop["frame"]!='do.01']   # auxiliary do.01 shouldn't be annotated, but sometimes is
        for prop in props:  # resolve relative clause * / LINK-PCR arguments    # TODO: ideally this would be done in preparing the JSON file (add_prop)
            # see wsj_0003.0 for an example ('workers' at 25:1 vs. '*' at 27:0 as the ARG1 of expose.01)
            
            empty2overt = {}
            for arg in prop["args"]:
                if arg[0]=='LINK-PCR':
                    overtNode, emptyNode = arg[1].split('*')[:2] # TODO: sometimes more than 2 chain members, e.g. in wsj_0003.10
                    empty2overt[emptyNode] = overtNode
            for arg in prop["args"]:
                if arg[0].startswith('ARG') and arg[4]=='*':
                    overtNode = empty2overt[arg[1]]
                    # look up node in the tree, convert to offsets
                    pt = SpanTree.parse(data["goldparse"])  # TODO: what if it is a non-OntoNotes (PTB) tree?
                    leaf_id, depth = pt.parse_pos(overtNode)
                    treepos = pt.get_treepos(leaf_id, depth)
                    overtWords = pt[treepos].leaves()
                    overtStart, overtEnd = span_from_treepos(pt, treepos)
                    if config.verbose: print('relative clause LINK-PCR: ',arg,'-->',(overtStart,overtEnd,overtWords), file=sys.stderr)
                    arg[1] = overtNode
                    arg[2], arg[3] = overtStart, overtEnd
                    arg[4] = ' '.join(overtWords)
        return props

def loadNProp(jsonFile):
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['nom']

def loadTimex(jsonFile):
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        return json.load(jsonF)['timex']

def loadDepParse(jsonFile):
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

        # dependency parse: un-collapse coordinate structures except for amod links
        conjs = [d for dep in deps if dep for d in dep if d["rel"].startswith('conj_')]
        if conjs:
            if config.verbose:
                print('resolving coordination...', file=sys.stderr)
            #print(tokens)
            ccs = [dep for dep in sentJ["stanford_dep_basic"] if dep["rel"]=='cc']
        for conj in conjs:
            i, r, h = conj["dep_idx"], conj["rel"], conj["gov_idx"]
            # note that the conjunction link connects two conjuncts
            # (the conjunction word is incorporated in the relation name,
            # but the conjunction token index is not represented)

            iextdeps = [dep for dep in deps[i] if not dep["rel"].startswith('conj')]
            assert len(iextdeps)==1,iextdeps
            iextdep = iextdeps[0]  # external (non-conjunction) head link of conjunction's dependent
            hextdeps = [dep for dep in deps[h] if not dep["rel"].startswith('conj')]
            assert len(hextdeps)<=1,hextdeps

            if r=='conj_and' and iextdep["rel"]=='amod': # remove this conjunction link
                if config.verbose: print('  removing',conj, file=sys.stderr)
                deps[i].remove(conj)
            else:   # undo propagation of conjunct dependencies
                # remove the non-conjunction link sharing a dependent with the conjunction link
                # example from wsj_0020.0: "removed Korea and Taiwan" transformed from
                #    removed <-dobj- Korea <-conj_and- Taiwan
                #        ^-------------------------dobj---|
                #  to
                #    removed <-dobj- Korea <-conj_and- Taiwan

                if hextdeps:
                    hextdep = hextdeps[0]  # external (non-conjunction) head link of conjunction's governor
                    if config.verbose: print('  removing',hextdep, file=sys.stderr)
                    deps[h].remove(hextdep)
                if config.verbose: print('  removing',iextdep, file=sys.stderr)
                deps[i].remove(iextdep)
                # then use Basic Dependencies to convert to
                #    removed <-dobj- and <-conj- Korea
                #                     ^----conj- Taiwan
                if config.verbose: print('  removing',conj, file=sys.stderr)
                deps[i].remove(conj)
                ccdeps = [dep for dep in ccs if dep["gov_idx"]==h]
                assert len(ccdeps)==1
                cc = ccdeps[0]
                c, cword = cc["dep_idx"], cc["dep"]
                conj0 = {"gov_idx": iextdep["gov_idx"], "gov": iextdep["gov"], "dep_idx": c, "dep": cword, "rel": iextdep["rel"]}
                if deps[c] is None:
                    deps[c] = []
                if conj0 not in deps[c]:
                    if config.verbose: print('  adding',conj0, file=sys.stderr)
                    deps[c].append(conj0)
                conj1 = {"gov_idx": c, "gov": cword, "dep_idx": h, "dep": ww[h], "rel": 'conj'}
                if conj1 not in deps[h]:
                    if config.verbose: print('  adding',conj1, file=sys.stderr)
                    deps[h].append(conj1)
                conj2 = {"gov_idx": c, "gov": cword, "dep_idx": i, "dep": ww[i], "rel": 'conj'}
                if config.verbose: print('  adding',conj2, file=sys.stderr)
                deps[i].append(conj2)

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

def loadCoref(jsonFile, ww):
    with codecs.open(jsonFile, 'r', 'utf-8') as jsonF:
        chains = json.load(jsonF)["coref_chains"]
        coref = {}  # coref chain ID -> set of elements
        for start,end,chainId,w in chains:
            coref.setdefault(chainId,set()).add((start,end,w))
            
        # TODO: some of the chains have overlapping members. requires further investigation, but for now just choose one of them.
        for chainId,chain in coref.items():
            itms = list(sorted(chain, key=lambda itm: itm[0]))  # sort by start index
            groups = [0] # group members of the chain that overlap
            for itm,pitm in zip(itms[1:],itms[:-1]):
                if itm[0]<=pitm[1]: # overlap
                    groups.append(groups[-1])
                else:
                    groups.append(groups[-1]+1) # new group
            for ig in range(groups[-1]+1):
                g = [itms[j] for j,i in enumerate(groups) if i==ig]
                if len(g):
                    choice = max(g, key=lambda itm: (itm[1], itm[1]-itm[0])) # choose the one that ends last, with the length as tiebreaker
                    for itm in g:
                        if itm!=choice:
                            chain.remove(itm)   # remove non-chosen members of the group
            
        return coref

#def parents(depParseEntry):
#    return [dep['dep_idx'] for dep in depParseEntry] if depParseEntry else []

def parent_edges(depParseEntry):
    return [(dep['gov_idx'],dep['dep_idx']) for dep in depParseEntry] if depParseEntry else []

def choose_head(tokenIndices, depParse, fallback=None):
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
    if len(frontier)>1 and fallback is not None:
        tiebroken = fallback(frontier)
        if tiebroken is not False:
            return tiebroken
    assert len(frontier)==1,(frontier,tokenIndices,[depParse[i] for i in frontier])
    return next(iter(frontier))

def mark_depths(depParse):
    '''
    For each node, mark its depth in the dependency parse, starting from 0 for the node with no parent.
    If a node has multiple parents its minimum depth is recorded (same for all dependency arcs into the child).
    '''
    children = defaultdict(set)
    roots = set()
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            i, h = dep["dep_idx"], dep["gov_idx"]
            children[h].add(i)
            if h is None:
                roots.add(i)
    assert len(roots)==1,roots
    
    def bfs(root, d=0):
        queue = [(root,d)]
        while queue:
            h, d = queue.pop(0)
            if "depth" not in depParse[h][0]:
                for dep in depParse[h]:
                    dep["depth"] = d
            for i in children[h]:
                if "depth" not in depParse[i][0]:
                    queue.append((i,d+1))
    
    bfs(next(iter(roots)))

def highest(tokenIndices, depParse):
    '''Of the given token indices, chooses the one corresponding to the node 
    that is highest in the dependency parse.'''
    frontier = set(tokenIndices)    # should end up with just 1 (the head)
    for itm in set(frontier):
        assert 0<=itm<len(depParse)
        if not depParse[itm]:
            frontier.remove(itm)
    dep = depParse[next(iter(frontier))][0]
    if "depth" not in dep:
        mark_depths(depParse)
    
    return min(frontier, key=lambda i: depParse[i][0]["depth"])

def new_amr(triples, concepts, roots=None):
    return Amr.from_triples(triples, concepts, roots=None, 
                            warn=(sys.stderr if config.verbose else None))  # only display AMR cycle warnings in verbose mode

def new_amr_from_old(oldamr, new_triples=[], new_concepts={}, avoid_triples=[], avoid_concepts=[], roots=None):
    '''Triples of the form (x,r,(y,)) or (x,r,y) are accepted.'''
    newconcepts = {v: c for v,c in oldamr.node_to_concepts.items() if v not in avoid_concepts}
    newconcepts.update(new_concepts)
    return new_amr([trip for trip in oldamr.triples(instances=None) if trip not in ensure_hyper(avoid_triples)]+new_triples,
                   newconcepts, roots=roots)

def ensure_hyper(triples):
    '''Generator over elements of triples, coercing items of the form (x,r,y) into the form (x,r,(y,)) 
    (the hyperedge-friendly representation used internally by Amr).'''
    for a,b,c in triples:
        if not isinstance(c,tuple):
            yield (a,b,(c,))
        yield (a,b,c)

def new_concept(concept, amr, alignment=None, alignedToken=None):
    '''
    Creates and returns a new (integer) variable for the designated concept, 
    though the variable is actually stored as a string in the AMR.
    Optionally updates an alignment, marking the specified token 
    as aligned to the new variable.
    '''
    x = len(amr.node_to_concepts)

    amr.node_to_concepts[str(x)] = concept

    if alignedToken is not None:
        alignment.link(x, alignedToken)

    return x    # variable, as an integer

def new_concept_from_token(amr, alignment, i, depParse, concept=None):
    '''
    If 'i' is an integer, aligning to the 'i'th token.
    If 'i' is an interable over integers, finds and aligns to 
    the common head of the indices in 'i'.
    If 'concept' is specified, that string will be used as the 
    concept name; otherwise, the aligned token will be used.
    '''
    h = choose_head(i, depParse) if hasattr(i, '__iter__') else i
    v = new_concept(token2concept(depParse[h][0]["dep"]) if concept is None else concept, amr, alignment, h)
    return v

def get_or_create_concept_from_token(amr, alignment, i, depParse, completed=None, concept=None):
    '''
    Like new_concept_from_token(), but doesn't modify the AMR if the 
    appropriate head token is already aligned to a variable.
    
    If the 'completed' data structure is provided, marks the token as completed.
    '''
    h = choose_head(i, depParse) if hasattr(i, '__iter__') else i
    v = alignment[:h] # index of variable associated with i's head, if any
    if not (v or v==0): # need a new variable
        if completed:
            assert not completed[0][h]
        v = new_concept(token2concept(depParse[h][0]["dep"]) if concept is None else concept, amr, alignment, h)
    if completed: completed[0][h] = True
    return v

if __name__=='__main__':
    args = sys.argv[1:]
    keepNombank = False # keep NomBank predicate names and arguments that cannot be verbalized
    while args and args[0][0]=='-':
        arg = args.pop(0)
        if arg=='-v':
            config.verbose = True
        elif arg=='-w':
            config.warn = True
        elif arg=='-e':
            config.errorTolerant = True
        elif arg=='-n':
            config.keepNombank = True
        elif arg=='-a':
            config.alignments = True
        else:
            assert False,'Unknown flag: '+arg
    
    files = [f for ff in args for f in glob.glob(ff)]
    main(files)
