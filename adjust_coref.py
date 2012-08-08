#!/usr/bin/env python

import sys
import json
import re

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    parser.add_argument('-verbose', action='store_true')
    arguments = parser.parse_args(sys.argv[1:])

    docId, sentNr = re.search(r'wsj_(\d+).(\d+).json', arguments.json).groups()
    sentNr = int(sentNr)
    data = json.load(open(arguments.json))

        #
        #for sentenceNr, sentenceCoref in enumerate(corefDict):
        #    for lCorefChain in sentenceCoref:
        #        lCorefChainTemp = []
        #        for lCorefPair in lCorefChain:
        #            refExpr = lCorefPair[0]
        #            antecedent = lCorefPair[1]

    assert not 'stanford_coref' in data
    data['stanford_coref'] = []
    if 'coref' in data:
        for sentence in data['coref']:
            for chain in sentence:
                data['stanford_coref'].append([])
                for entry in chain:
                    #print pair
                    if len(entry) == 5:
                        entry = entry[0:1] + entry[3:]
                        data['stanford_coref'][-1].append(entry)

        data.pop('coref')

    for cchain in data['coref_chains']:
        cchain.pop()

    json.dump(data, open(arguments.jsonout, 'w'), indent=2)
