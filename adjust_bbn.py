#!/usr/bin/env python

import sys
import json

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('json', action='store', help="json input file")
    parser.add_argument('jsonout', action='store', help="json output file")
    parser.add_argument('-verbose', action='store_true')
    arguments = parser.parse_args(sys.argv[1:])

    data = json.load(open(arguments.json))


    for ne in data['bbn_ne']:
        assert len(ne) == 7, "already stipped elements? ne:%s\n" %(str(ne))
        ne.pop()
        ne.pop()

    json.dump(data, open(arguments.jsonout, 'w'), indent=2)
