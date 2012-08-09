from amr import Amr
import itertools
import math
import sys
import random
import copy
import pyparsing

def get_mappings(l2, l1):
     if len(l2) >= len(l1):
         return (zip(t,l1) for t in itertools.permutations(l2, len(l1)))
     else:
         return (zip(l2,l) for l in itertools.permutations(l1, len(l2)))

def get_random_start(l2,l1):
     if len(l2) >= len(l1):
         random.shuffle(l1)
         return zip(l2,l1)        
     else:
         random.shuffle(l2)
         return zip(l2, l1)


def compute_score(triples1, triples2):
    """
    Compute precision, recall, and f-score. Variable names must be identical.
    """
    t1 = set(triples1)
    t2 = set(triples2)
    prec = len(t1.intersection(t2)) / float(len(t2))
    rec = len(t1.intersection(t2)) / float(len(t1))
    if prec == 0.0 and rec == 0.0:
        return 0.0, 0.0, 0.0 
    f = 2 * prec * rec  / (prec + rec)
    return prec, rec, f

def compute_score_and_matching_vars(amr1, amr2, mapping):
    """
    Compute precision, recall, and f-score. Variable names must be identical.
    """
    inv_map = dict((v,k) for (k,v) in mapping.items())

    test_amr = amr1.apply_node_map(mapping)
    

    t1 = set(test_amr.triples())
    for r in test_amr.roots: 
        t1.add((r,"TOP",test_amr.node_to_concepts[r]))
    t2 = set(amr2.triples())
    for r in amr2.roots: 
        t2.add((r,"TOP",amr2.node_to_concepts[r]))

    common = t1.intersection(t2)


    prec = len(common) / float(len(t1))
    rec = len(common) / float(len(t2))
    if prec == 0.0 and rec == 0.0:
        return 0.0, 0.0, 0.0, []
    f = 2 * prec * rec  / (prec + rec)

    matching = set()
    for p,r,c in common:
        if p in inv_map: 
            matching.add((inv_map[p],p))        
        if type(c) is tuple:
            for child in c: 
                if child in inv_map:
                    matching.add((inv_map[child],child))
            else:
                if c in inv_map:
                    matching.add((inv_map[c],c))

    return prec, rec, f, matching
    

def compute_smatch_precise(amr1, amr2):
    nodes1 = amr1.get_nodes()
    nodes2 = amr2.get_nodes()
    # map nodes1 to nodes2
    best_f = 0.0
    prec_with_best_f = 0.0
    rec_with_best_f = 0.0
    mappings = list(get_mappings(nodes1, nodes2))
    for mapping_tuples in mappings: 
        sys.stdout.write(".")
        mapping = dict(mapping_tuples)
        new_amr1 = amr1.apply_node_map(mapping)
        prec, rec, f = compute_score(new_amr1.triples(), amr2.triples())
        if f >= best_f:
            best_f = f
            prec_with_best_f = prec
            rec_with_best_f = rec
    sys.stdout.write("\n")
    return prec_with_best_f, rec_with_best_f, best_f

def compute_smatch_hill_climbing(amr1in, amr2in, starts = 10):       
    """
    Run hill climbing search in the space of variable mappings to find the smatch score between two AMRs.

    >>> amr1 = Amr.from_string("(a / amr-unknown :domain-of (x1 / population-quantity) :quant-of (x0 / people :loc-of (b / state :name (x2 / name :op0 (washington / washington) ))))")
    >>> amr2 = Amr.from_string("(t / amr-unknown :domain-of (x11 / density-quantity) :loc (x60 / state :name (x13 / name :op0 (x12 / washington) )))")
    >>> compute_smatch_hill_climbing(amr1,amr2, starts = 10) 
    (0.6666666666666666, 0.8, 0.7272727272727272)
    """

        
    amr1 = amr1in.clone_canonical(prefix="t")
    amr2 = amr2in.clone_canonical(prefix="g")

    best_f = -1.0 
    prec_with_best_f = 0.0
    rec_with_best_f = 0.0
    nodes1 = amr1.get_nodes()
    nodes2 = amr2.get_nodes()
    best_mapping =  {}

    for i in range(starts):
        mapping_tuples = get_random_start(nodes1, nodes2)    
    
        mapping = dict(mapping_tuples)
        max_prec, max_rec, max_f, matching_tuples = compute_score_and_matching_vars(amr1, amr2, mapping)

        prev_f = -1.0
        

        while max_f > prev_f:

            prev_f = max_f
            matching_dict = dict(matching_tuples)
            left_in_a1 = [n for n in nodes1 if not n in matching_dict.keys()]
            left_in_a2 = [n for n in nodes2 if not n in matching_dict.values()]           

            # Do step
            for x in left_in_a1: # Explore all neighbors                    
                for y in left_in_a2:        
                    try_mapping = copy.copy(matching_dict)
                    try_mapping[x] = y 
                    prec, rec, f, try_matching_tuples = compute_score_and_matching_vars(amr1,amr2, try_mapping)
                    if f > max_f: #Keep the triple
                        max_prec = prec
                        max_rec = rec
                        matching_tuples = try_matching_tuples
                        mapping = try_mapping
                        max_f = f

        if prev_f > best_f:
                best_f = prev_f
                prec_with_best_f = max_prec
                rec_with_best_f = max_rec
                best_mapping = mapping

    return prec_with_best_f, rec_with_best_f, best_f

def mean(l):
    if len(l)==0:
        return float("NaN")
    else:
        return math.fsum(l) / len(l)


def compute_smatch_batch(gold_filename, test_filename):
     ps, rs, fs = [], [],[]
     with open(sys.argv[1]) as gold_file:
            with open(sys.argv[2]) as test_file:
                gold = gold_file.readline().strip()
                test = test_file.readline().strip()
        
                tiburonfailct = 0
                parsefailct = 0
                totalct = 0

                while gold: 
                    totalct += 1
                    if gold and test: 
                        try:
                            p,r,f = compute_smatch_hill_climbing(amr_gold, amr_test)
                            #hill_climbing(amr_gold, amr_test)
                            print "P:%f R:%f F:%f " % (p, r, f) 
                            ps.append(p)
                            rs.append(r)
                            fs.append(f)
                        except pyparsing.ParseException:
                            sys.stderr.write("Cannot parse amr '%s'.\n" % test)    
                            parsefailct += 1

                    else: 
                        tiburonfailct += 1
                    gold = gold_file.readline().strip()
                    test = test_file.readline().strip()
                    
     avgp = mean(ps)
     avgr = mean(rs)
     avgf = mean(fs)
     print "MEAN SMATCH: P:%f R:%f F:%f " % (avgp, avgr, avgf)
     print "Total: %i   Fail(tiburon): %i   Fail(invalid AMR): %i "  % (totalct, tiburonfailct, parsefailct)


if __name__ == "__main__":
        import doctest
        doctest.testmod()

