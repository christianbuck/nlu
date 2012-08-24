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
    import nes, timex, vprop, nprop, verbalize, conjunctions, copulas, adjsAndAdverbs, auxes, misc, coref, top, beautify
    
    nSents = len(files)
    nSuccess = nConnected = 0
    iSent = 0
    
    def wsj_sort(path):
        m = re.search(r'wsj_(\d{4})\.(\d+)', path)
        if not m: return 0
        docnum, sentnum = m.groups()
        return (int(docnum), int(sentnum))

    for f in sorted(files,key=wsj_sort):

        try:
            sentenceId = os.path.basename(f).replace('.json','')
            
            if config.showSentence:
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
            
            # the sentence
            if config.showSentence:
                print(' '.join(filter(None,ww)))
                print()
                sys.stdout.flush()

            hasModuleException = False
            for m in [nes, timex, vprop, nprop, verbalize, conjunctions, copulas, adjsAndAdverbs, auxes, misc, coref, top, beautify]:
                if config.verbose:
                    print('\n\nSTAGE: ', m.__name__, '...', file=sys.stderr)
                    
                try:
                    depParse, amr, alignments, completed = m.main(sentenceId, f, tokens, ww, wTags, depParse, amr, alignments, completed)
                except Exception as ex:
                    hasModuleException = True
                    if not config.errorTolerant:
                        raise
                    print('EXCEPTION IN', m.__name__, 'MODULE\n', file=sys.stderr)
                    print(sentenceId, file=sys.stderr)
                    traceback.print_exception(*sys.exc_info())
                
                if config.verbose:
                    print(repr(amr), file=sys.stderr)
                    print('Completed:',[depParse[i][0]['dep'] for i,v in enumerate(completed[0]) if v and depParse[i]], file=sys.stderr)
                    print(alignments, [deps[0]['dep'] for deps in depParse if deps and not completed[0][deps[0]['dep_idx']]], file=sys.stderr)
                    print(amr, file=sys.stderr)
                
            if config.verbose:
                print(' '.join(tokens), file=sys.stderr)

            if amr.is_connected(warn=None):
                nConnected += 1
            else:
                # insert dummy top node, called 'and' for now. remove :-DUMMY triples for (former) orphans.
                amr = new_amr_from_old(amr, new_triples=[('top','opX',v) for v in amr.roots], new_concepts={'top': 'and'}, avoid_triples=[(x,r,(y,)) for x,r,(y,) in amr.triples(instances=False) if r=='-DUMMY'])

            print(amr)
            #amr.render()
            #print('Amr.from_triples(',amr.triples(instances=False),',',amr.node_to_concepts,')')
            print()
            if config.alignments:
                print(alignments)
                print()
    
            if config.verbose or config.showRemainingDeps:
                print('\n\nRemaining edges:', file=sys.stderr)
                for deps in depParse:
                    if deps is None: continue
                    for dep in deps:
                        if dep['gov_idx'] is not None and not completed[1][(dep['gov_idx'],dep['dep_idx'])]:
                            print((dep['gov']+'-'+str(dep['gov_idx']),dep['rel'],dep['dep']+'-'+str(dep['dep_idx'])), file=sys.stderr)

            if not hasModuleException:
                nSuccess += 1

            
        except Exception as ex:
            if not config.errorTolerant:
                raise
            print('(x1 / amr-empty)\n')
            print(sentenceId, file=sys.stderr)
            traceback.print_exception(*sys.exc_info())
            time.sleep(0)
            
        iSent += 1
        print('{}/{}, {} succeeded without exceptions ({} connected)'.format(iSent, nSents, nSuccess, nConnected), file=sys.stderr)

def token2concept(t, normalize_pronouns=True):
    t = t.replace('$', '-DOLLAR-')
    res =  re.sub(r'[^A-Za-z0-9-]', '', t).lower() or '??'
    if res=='??':
        assert False, t
    PRONS = {'me': 'i', 'my': 'i', 'us': 'we', 'our': 'we', 
             'your': 'you', 'them': 'they', 'their': 'they', 
             'him': 'he', 'his': 'he', 'her': 'she', 'its': 'it',
             'these': 'this', 'those': 'that'}   # TODO: mine, hers, etc.?
    res = PRONS.get(res, res)
    if res in PRONS.values():   # Will also apply to demonstrative determiners, which should be kept as :mod's.
        res += '-FALLBACK_PRON'  # Pronouns should be dispreferred as concept heads.
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


        mark_depths(deps)

        # dependency parse: un-collapse coordinate structures except for amod links
        conjs = [d for dep in deps if dep for d in dep if d["rel"].startswith('conj_')]
        if conjs:
            if config.verbose:
                print('resolving coordination...', file=sys.stderr)
            #print(tokens)
            ccs = [dep for dep in sentJ["stanford_dep_basic"] if dep["rel"]=='cc']
            
        
        # account for coordinations with >2 conjuncts: group together  
        # under the head of the coordinate structure (one of the conjuncts)
        conjgroups = defaultdict(lambda: [set(), set()])
        for conj in conjs:
            i, r, h = conj["dep_idx"], conj["rel"], conj["gov_idx"]
            if [dep for dep in sentJ["stanford_dep_basic"] if dep["dep_idx"]==i and dep["gov_idx"]==h and dep["rel"]=='conj']:
                conjgroups[(h,r)][0].add(i)
            else:   # i is a modifier of the whole coordinate phrase. see comment below for an example.
                conjmodifiers = [dep for dep in sentJ["stanford_dep_basic"] if dep["dep_idx"]==i and dep["gov_idx"]==h]
                assert len(conjmodifiers)==1
                conjmodifier = conjmodifiers[0]
                # remove the 'conj' edge from the collapsed parse
                deps[conjmodifier["dep_idx"]] = [dep for dep in deps[conjmodifier["dep_idx"]] if dep["gov_idx"]!=h]
                conjgroups[(h,r)][1].add((conjmodifier["dep_idx"], conjmodifier["rel"]))
        
        for (h,r),(ii,mm) in sorted(conjgroups.items(), key=lambda ((h,r),ii): deps[h][0]["depth"]):
            assert h>0
            # find the collapsed dependencies, i.e. the (non-conjunction) links shared 
            # by all conjuncts. start with higher nodes in the tree in case there are 
            # coordinations embedded within coordinations (cf. wsj_0003.25).
            isharedheads = {g: gdep for g,gdep in parent_deps(deps[h]) if all(g in parents(deps[i]) for i in ii)}
            if None in parents(deps[h]):  # h is the root token
                assert not isharedheads
                isharedheads = {None: dict(parent_deps(deps[h]))[None]}
            else:
                assert isharedheads,((ww[h],parents(deps[h]),r),[(ww[i],parents(deps[i])) for i in ii])
            
            # special treatment for and-ed adjectival modifiers
            if r=='conj_and':
                amodConj = False
                for g,gdep in isharedheads.items():
                    if gdep["rel"]=='amod':  # remove the conjunction link(s)
                        amodConj = True
                        for i in ii:
                            if config.verbose: print('  removing',r,'link (gov',h,', dep',i,')', file=sys.stderr)
                            deps[i] = [d for d in deps[i] if d["rel"]!=r]
                        break
                if amodConj:
                    continue
            
            # everything else: undo propagation of conjunct dependencies
            
            
            # 1. remove the non-conjunction link sharing a dependent with the conjunction link
            # example from wsj_0020.0: "removed Korea and Taiwan" transformed from
            #    removed <-dobj- Korea <-conj_and- Taiwan
            #        ^-------------------------dobj---|
            #  to
            #    removed         Korea <-conj_and- Taiwan
            # (Korea is h, Taiwan is its dependent i, removed is the shared head)
            
            for isharedhead in isharedheads:
                for i in {h} | ii:
                    if config.verbose: print('  removing any links with (gov',isharedhead,', dep',i,')', file=sys.stderr)
                    deps[i] = [d for d in deps[i] if d["gov_idx"]!=isharedhead]
            
            # 2. then use Basic Dependencies to convert to
            #    removed <-dobj- and <-conj- Korea
            #                     ^----conj- Taiwan
            
            # - get the coordinating conjunction (call its index c)
            ccdeps = [dep for dep in ccs if dep["gov_idx"]==h]
            assert len(ccdeps)==1
            cc = ccdeps[0]
            c, cword = cc["dep_idx"], cc["dep"]
            if deps[c] is None: deps[c] = []
            
            # conjmodifiers: anything that modifies the head conjunct with type conj_* in the collapsed parse 
            # but another type (such as advmod) in the basic parse is a modifier of the entire coordinate phrase.
            # therefore, attach to the coordinating conjunction.
            # arises in wsj_0003.25 ('dumped..., poured... and mechanically mixed': 'mechanically' is converted to 
            # an advmod of the whole phrase, which is probably not correct but would be a valid interpretation if 
            # the word order were slightly different).
            for (imod,modrel) in mm:
                deps[imod].append({"gov_idx": c, "gov": cword, "dep_idx": imod, "dep": ww[imod], "rel": modrel})
            
            # - link coordinating conjunction to the shared heads, in place of h
            for isharedhead,sharedheaddep in isharedheads.items():
                deps[c].append({"gov_idx": sharedheaddep["gov_idx"], "gov": sharedheaddep["gov"], "dep_idx": c, "dep": cword, "rel": sharedheaddep["rel"]})
                deps[h].append({"gov_idx": c, "gov": cword, "dep_idx": h, "dep": ww[h], "rel": 'conj'})
                for i in ii:
                    deps[i].append({"gov_idx": c, "gov": cword, "dep_idx": i, "dep": ww[i], "rel": 'conj'})

            # 3. Remove conj_* links
            for i in ii:
                if config.verbose: print('  removing any conj_* links with (gov',h,', dep',i,')', file=sys.stderr)
                deps[i] = [d for d in deps[i] if d["gov_idx"]!=h or not d["rel"].startswith('conj_')]

            clear_depths(deps)
            mark_depths(deps)

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

def parents(depParseEntry):
    return [dep["gov_idx"] for dep in depParseEntry] if depParseEntry else []

def parent_edges(depParseEntry):
    return [(dep["gov_idx"],dep["dep_idx"]) for dep in depParseEntry] if depParseEntry else []

def parent_deps(depParseEntry):
    return [(dep["gov_idx"],dep) for dep in depParseEntry] if depParseEntry else []

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

def clear_depths(depParse):
    for deps in depParse:
        if deps is None: continue
        for dep in deps:
            if "depth" in dep:
                del dep["depth"]

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
    return Amr.from_triples(ensure_quant(triples), concepts, roots=None, 
                            warn=(sys.stderr if config.verbose else None))  # only display AMR cycle warnings in verbose mode

def new_amr_from_old(oldamr, new_triples=[], new_concepts={}, avoid_triples=[], avoid_concepts=[], roots=None):
    '''Triples of the form (x,r,(y,)) or (x,r,y) are accepted.'''
    newconcepts = {v: c for v,c in oldamr.node_to_concepts.items() if v not in avoid_concepts}
    newconcepts.update(new_concepts)
    return new_amr([trip for trip in oldamr.triples(instances=None) if trip not in ensure_quant(avoid_triples)] \
                    + list(ensure_quant(new_triples)),
                   newconcepts, roots=roots)

def ensure_hyper(triples):
    '''Generator over elements of triples, coercing items of the form (x,r,y) into the form (x,r,(y,)) 
    (the hyperedge-friendly representation used internally by Amr).'''
    for a,b,c in triples:
        if not isinstance(c,tuple):
            yield (a,b,(c,))
        else:
            yield (a,b,c)

class Atom(object):
    '''Wrapper for atomic values in AMRs, such as numeric quantities and the special symbol '-'. 
    This ensures that if a value occurs multiple times, those are not treated as identical 
    (i.e. the same node) for the purpose of printing AMRs.'''
    def __init__(self, v):
        self._v = v
    def __str__(self):
        return str(self._v)
    def __repr__(self):
        return repr(self._v)
    def __eq__(self, that):
        '''Tests as equal to the bare value, as well as to other Atoms with equal bare values'''
        return that==self._v

def ensure_quant(triples):
    for trip in ensure_hyper(triples):
        a,b,(c,) = trip
        if isinstance(c,(int,float)):
            yield (a,b,(Atom(c),))
        else:
            yield (a,b,(c,))

def new_concept(concept, amr):
    '''
    Creates and returns a new (integer) variable for the designated concept, 
    though the variable is actually stored as a string in the AMR.
    '''
    v = len(amr.node_to_concepts)

    amr.node_to_concepts[str(v)] = concept

    return v    # variable, as an integer

def new_concept_from_token(amr, alignment, i, depParse, wTags, concept=None):
    '''
    If 'i' is an integer, aligning to the 'i'th token.
    If 'i' is an interable over integers, finds and aligns to 
    the common head of the indices in 'i'.
    If 'concept' is specified, that string will be used as the 
    concept name; otherwise, the aligned token's lemma will be used.
    @return: Integer variable for the new concept
    '''
    h = choose_head(i, depParse) if hasattr(i, '__iter__') else i
    v = new_concept(token2concept(wTags[h]["Lemma"]) if concept is None else concept, amr)
    alignment.link(v, h)
    return v

def get_or_create_concept_from_token(amr, alignment, i, depParse, wTags, completed=None, concept=None):
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
        v = new_concept(token2concept(wTags[h]["Lemma"]) if concept is None else concept, amr)
        alignment.link(v, h)
    if completed: completed[0][h] = True
    return v

if __name__=='__main__':
    args = sys.argv[1:]
    fullNombank = False # include NomBank predicate names and arguments that cannot be verbalized
    while args and args[0][0]=='-':
        arg = args.pop(0)
        if arg=='-v':
            config.verbose = True
        elif arg=='-w':
            config.warn = True
        elif arg=='-r':
            config.showRemainingDeps = True
        elif arg=='-e':
            config.errorTolerant = True
        elif arg=='-n':
            config.fullNombank = True
        elif arg=='-a':
            config.alignments = True
        elif arg=='-S':
            config.showSentence = False
        else:
            assert False,'Unknown flag: '+arg
    
    files = [f for ff in args for f in glob.glob(ff)]
    main(files)
