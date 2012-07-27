#!/usr/bin/env python

import sys
import json
from collections import defaultdict
from itertools import imap, izip
from nltk.tree import Tree
import re

class SpanTree(Tree):
    """
    Tree with added get_span functionality.
    This requires you to call 'convert' on the
    root node.
    """

    def convert(self): # todo: better name
        """
        replace leaf label with numbers to we can
        easily read the spans from subtrees
        """
        for i, pos in enumerate(self.treepositions('leaves')):
            self[pos] = i
        self.enumerated = True

    def get_span(self):
        """
        returns the span of the (sub-)tree
        (0,0) is only the first word
        (0,1) are the first two words
        """
        return (min(self.leaves()), max(self.leaves()))

    def span_is_subtree(self, start, end):
        for st in self.subtrees():
            st_start, st_end = st.get_span()
            if st_start == start and st_end == end:
                return True
        return False

class DictTree(Tree):
    """
    Tree
    """

class Sentence(object):
    """
    holds all annotations for a single sentence.
    """

    def __init__(self, json_file):
        data = json.load(json_file)
        for k, v in data.iteritems():
            self.__setattr__(k, v)
        self.__raw_data = data # for future reference

        #print data
        self.spantree = SpanTree.parse(self.goldparse)
        self.spantree.convert()
        self.goldparse = Tree.parse(self.goldparse)

        self.text = data['text'].split()
        self.treebank_sentence = data['treebank_sentence'].split()

        #self.check()
        #print self.parsetree.get_span()

    def check(self):
        """
        perform data consistency checks
        """
        self.check_ne_spans()

    def check_ne_spans(self):
        for ne in self.bbn_ne:
            start, end = ne[0:2]
            is_span = self.spantree.span_is_subtree(start, end)
            if is_span:
                #print "NE \"%s\" (%s-%s) is subtree" %(ne[2],ne[0],ne[1])
                pass
            else:
                print "NE \"%s\" (%s-%s) is not subtree" %(ne[2],ne[0],ne[1])
                print ne
                self.goldparse.draw()



class DepOffset(object):
    def __init__(self, s1, s2):
        assert len(s2) >= len(s1)
        self.mapping = [0]
        self.__max_in = len(s1)
        self.__max_out = len(s2)

        offset = 0
        for i1, w1 in enumerate(s1):
            i2 = offset + i1
            while i2 < len(s2) and s2[i2] != w1:
                offset += 1
                i2 = offset + i1
            if i2 >= len(s2):
                return False
            assert s1[i1] == s2[i2]
            #print i2+1, s2[i2]
            self.mapping.append(i2+1) # indices start from 1
        #print self.mapping
        assert len(self.mapping) == self.__max_in + 1

    def map_to_longer(self, idx):
        assert idx >= 0, "idx should be in [0,%s]" %self.__max_in
        assert idx <= self.__max_in, "idx should be in [0,%s]" %self.__max_in
        return self.mapping[idx]

class Dependencies(object):
    pass

def read_dependencies(filename, n, offsets=None):
    """ reads stuff like this:

    nn(Agnew-2, Rudolph-1)
    nsubjpass(named-17, Agnew-2)
    num(years-5, 55-4)
    """
    dependencies = []
    assert n >= 1, 'use numbering starting from 1'
    re_dep = re.compile(r'^(\S+)\((\S+)-(\d+), (\S+)-(\d+)\)$')
    deps = open(filename).read().split('\n\n')[n-1]
    for line in imap(str.strip, deps.split('\n')):
        if not line:
            continue
        m = re_dep.match(line)
        assert m, "strange line: %s" %line
        rel, gov, gov_idx, dep, dep_idx = m.groups()
        dep_idx = int(dep_idx)
        gov_idx = int(gov_idx)
        if offsets != None:
            dep_idx = offsets.map_to_longer(dep_idx)
            gov_idx = offsets.map_to_longer(gov_idx)
        dependencies.append( {'rel': rel,
                              'dep': dep,
                              'dep_idx' : dep_idx,
                              'gov' : gov,
                              'gov_idx' : gov_idx} )
    #for entry in dependencies:
    #    print entry
    return dependencies

def add_to_json(infile, outfile, key, value):
    data = json.load(open(infile))
    data[key] = value
    json.dump(data, open(outfile,'w'), indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    #parser.add_argument('depfile', action='store', help="dependencies input file")
    parser.add_argument('jsonfile', action='store', help="json input file")
    parser.add_argument('outfile', action='store', help="output file")
    args = parser.parse_args(sys.argv[1:])

    s = Sentence(open(args.jsonfile))
    off = DepOffset(s.text, s.treebank_sentence)
    n = int(args.jsonfile.split('.')[-2])
    depfile = args.jsonfile.rsplit('.',2)[0] + '.dep'
    print 'depfile:', depfile
    #sys.exit()
    dependencies = read_dependencies(depfile, n, off)
    add_to_json(args.jsonfile, args.outfile, 'stanford_dep', dependencies)
