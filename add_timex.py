#!/usr/bin/env python

import sys
from collections import defaultdict
from itertools import imap, izip
import json
import re
from spantree import SpanTree
from xml.etree import ElementTree

def find_spans(sentence, force_adjusted_idx=True):
    spans = defaultdict(list)
    expressions = {}
    for word_id, (word, annotation) in enumerate(sentence['words']):
        if 'Timex' in annotation:
            timex = ElementTree.fromstring(annotation['Timex'])
            tid = timex.attrib['tid']
            expressions[tid] = annotation['Timex']
            if 'idx' in annotation:
                spans[tid].append(annotation['idx'])
            else:
                assert not force_adjusted_idx, 'idx not found in %s\n' %str(annotation)
                spans[tid].append(word_id)
    return spans, expressions

def process_file(json_filename):
    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', json_filename).groups()
    sentNr = int(sentNr)
    data = json.load(open(json_filename))
    spans, expressions = find_spans(data)

    data['timex'] = []
    for tid in spans:
        data['timex'].append( [tid, min(spans[tid]), max(spans[tid]), expressions[tid]])
    print data['timex']

    json.dump(data, open(json_filename, 'w'), indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', nargs='+', help="json input file")
    arguments = parser.parse_args(sys.argv[1:])


    for filename in arguments.json:
        print filename, '...'
        process_file(filename)
