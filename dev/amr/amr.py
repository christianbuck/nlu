'''
Abstract Meaning Representation

@author: Daniel Bauer (dbauer)
@author: Nathan Schneider (nschneid)
@since: 2012-06-18
'''

from dag import Dag
from amr_parser import make_amr_parser, SpecialValue, StrLiteral

from collections import defaultdict
import pyparsing
import unittest
import re
import sys
import copy

def print_amr_error(amr_str):
    sys.stderr.write("Could not parse AMR.\n")
    sys.stderr.write(amr_str)    
    sys.stderr.write("\n")

class Amr(Dag):
    """
    An abstract meaning representation.
    The structure consists of nested mappings from role names to fillers.
    Because a concept may have multiple roles with the same name, 
    a ListMap data structure holds a list of fillers for each role.
    A set of (concept, role, filler) triples can be extracted as well.
    """
    _parser_singleton = None

    def __init__(self, *args, **kwargs):       
        super(Amr, self).__init__(*args, **kwargs)
        self.node_to_concepts = {}

    def apply_node_map(self, node_map):
        """
        Needed for smatch.
        """
        new = Dag.apply_node_map(self, node_map)
        new.__class__ = Amr
        new.node_to_concepts = {}
        for n in self.node_to_concepts:
            if n in node_map:
                new.node_to_concepts[node_map[n]] = self.node_to_concepts[n]
            else:
               new.node_to_concepts[n] = self.node_to_concepts[n]
        return new

    @classmethod
    def from_string(cls, amr_string):
        """
        Initialize a new abstract meaning representation from a Pennman style string.
        """
        if not cls._parser_singleton: # Initialize the AMR parser only once
            _parser_singleton = make_amr_parser()           
        try:
            ast = _parser_singleton.parseString(amr_string)
        except pyparsing.ParseException, e:
            sys.stderr.write("Could not parse AMR: %s" % amr_string)
            raise e 
        return ast_to_amr(ast)

    @classmethod
    def from_concept_edge_labels(cls, amr):
        """
        Create a new AMR from an AMR or a DAG in which concepts are pushed into incoming edges.
        """
        new_amr = amr.clone()
        new_amr.node_to_concepts = {}
        for par, rel, child in amr.triples():
           if type(rel) is str:    
                part1, part2 = rel.rsplit(":",1)        
                if part2: 
                    if part1.lower() != "root":
                        new_amr._replace_triple(par, rel, child, par, part1, child)
                    new_amr.node_to_concepts[child] = part2
                if part1.lower() == "root":
                    new_amr.roots.remove(par)
                    new_amr._remove_triple(par, rel, child)
                    new_amr.roots.add(child)
        return new_amr

    def to_concept_edge_labels(self):
        """"
        Return an new DAG with equivalent structure as this AMR (plus additional root-edge), in
        which concepts are pushed into incoming edges.
        """

        new_amr = self.clone_as_dag()
        for par, rel, child in self.triples(instances = False):
           #new_rel = "%s:%s" % (rel, ":".join(self.node_to_concepts[c] for c in child if c in self.node_to_concepts))
           new_rel = '%s:%s' % (rel, ':'.join(self.node_to_concepts[c] if c in self.node_to_concepts else c for c in child))
           new_amr._replace_triple(par,rel,child, par, new_rel, child)
        for r in self.roots:
            count = 0
            if r in self.node_to_concepts:
                new_rel = "ROOT:%s" % "".join(self.node_to_concepts[r])
            else: 
                new_rel = "ROOT"
            new_amr._add_triple('root%i' % count, new_rel, r)
            new_amr.roots.remove(r)
            new_amr.roots.append('root%i' % count)
            count += 1
        return new_amr

    def stringify(self):
        """
        Convert all special symbols in the AMR to strings.
        """
        
        new_amr = Amr()

        def conv(node): # Closure over new_amr
            if isinstance(node, StrLiteral):
                var =  str(node)[1:-1] 
                new_amr._set_concept(var, str(node))
                return var
            else: 
                return str(node)

        for p,r,c in self.triples(instances = False):
            c_new = tuple([conv(child) for child in c]) if type(c) is tuple else conv(c)
            p_new = conv(p)
            new_amr._add_triple(p_new, r, c_new)

        new_amr.roots = [conv(r) for r in self.roots]
        new_amr.external_nodes = [conv(r) for r in self.external_nodes]
        for node in self.node_to_concepts:    
            new_amr._set_concept(conv(node), self.node_to_concepts[node])
        return new_amr    

    @classmethod
    def from_triples(cls, triples, concepts, roots = None):
        """
        Initialize a new abstract meaning representation from a collection of triples 
        and a node to concept map.
        """
        amr = Dag.from_triples(triples, roots)
        amr.__class__ = Amr
        amr.node_to_concepts = concepts
        return amr

    def get_concept(self, node):
        """
        Retrieve the concept name for a node.
        """
        return self.node_to_concepts[node]
    
    def _set_concept(self, node, concept):
        """
        Set concept name for a node.
        """
        self.node_to_concepts[node] = concept

    def triples(self, instances = True, start_node = None):
        """
        Retrieve a list of (node, role, filler) triples. If instances is False
        do not include 'instance' roles.
        """
        res = [t for t in super(Amr, self).triples(start_node)]
        if instances:
            for node, concept in self.node_to_concepts.items():
                res.append((node, 'instance', concept))
        return res

    def __str__(self):
        def extractor(node, firsthit, leaf):
            if node is None:
                    return "root"
            if type(node) is tuple or type(node) is list: 
                return ",".join("@%s" % (n) if n in self.external_nodes else n for n in node)
            else: 
                if type(node) is int or type(node) is float or isinstance(node, (SpecialValue, StrLiteral)):
                    return str(node)
                else: 
                    if firsthit and node in self.node_to_concepts: 
                        concept = self.node_to_concepts[node]
                        if not self[node]:
                            if node in self.external_nodes:
                                return "(@%s / %s) " % (node, concept)
                            else:
                                return "(%s / %s) " % (node, concept)
                        else: 
                            if node in self.external_nodes:    
                                return "@%s / %s " % (node, concept)
                            else:
                                return "%s / %s " % (node, concept)
                    else:
                        if node in self.external_nodes:
                            return "@%s" % node 
                        else:
                            return "%s" % node


        def combiner(nodestr, childmap, depth):
            childstr = " ".join(["\n%s :%s %s" % (depth * "\t", rel, child) for rel, child in sorted(childmap.items())])            
            return "(%s %s)" % (nodestr, childstr)

        def hedgecombiner(nodes):
             return " ,".join(nodes)

        return "\n".join(self.dfs(extractor, combiner, hedgecombiner))
    
    def to_string(self, newline = False):
         if newline:
             return str(self)
         else:
             return re.sub("(\n|\s+)"," ",str(self))

    def get_dot(self, instances = True):
        """
        Return a graphviz dot representation.
        """
        return self._get_gv_graph(instances).to_string()
    
    def _get_gv_graph(self, instances = True):
        """
        Return a pygraphviz AGraph.
        """        
        graph = pgv.AGraph(strict=False,directed=True)
        graph.node_attr.update(height=0.1, width=0.1, shape='none')
        graph.edge_attr.update(fontsize='9')
        for node, rel, child in self.triples(instances):
           nodestr, childstr = node, child
           if not instances:
                if node in self.node_to_concepts: 
                    nodestr = "%s / %s" % (node, self.node_to_concepts[node])
                if child in self.node_to_concepts:
                    childstr = "%s / %s" % (child, self.node_to_concepts[child])
           graph.add_edge(nodestr, childstr, label=":%s"%rel)
        return graph
   
    def render(self, instances = True):
        """
        Interactively view the graph. 
        """
        dot = self.get_dot(instances)
        window = xdot.DotWindow()
        window.set_dotcode(dot)
    
    def render_to_file(self, file_or_name, instances = True, *args, **kwargs):
        """
        Save graph to file
        """
        graph = self._get_gv_graph(instances)
        graph.draw(file_or_name, prog="dot", *args, **kwargs)
    
    def clone(self):
        """
        Return a deep copy of the AMR.
        """
        new = Amr() 
        new.roots = copy.copy(self.roots)
        new.external_nodes = copy.copy(self.external_nodes)
        new.node_to_concepts = copy.copy(self.node_to_concepts)
        for triple in self.triples(instances = False):
            new._add_triple(*copy.copy(triple))        
        return new

    def clone_as_dag(self, instances = True):        
        """
        Return a copy of the AMR as DAG.
        """
        new = Dag()
        
        for triple in self.triples(instances = False): 
            new._add_triple(*copy.copy(triple))
        new.roots = copy.copy(self.roots)
        new.external_nodes = copy.copy(self.external_nodes)
        return new

    def clone_canonical(self, external_dict = {}, prefix = ""):
        """
        Return a version of the DAG where all nodes have been replaced with canonical IDs.
        """
        new = Amr()
        node_map = self._get_canonical_nodes(prefix)
        for k,v in external_dict.items():
                node_map[k] = v
        new.roots = [node_map[x] for x in self.roots]
        new.external_nodes = set([node_map[x] for x in self.external_nodes])
        for par, rel, child in self.triples(instances = False):
            if type(child) is tuple:                 
                new._add_triple(node_map[par], rel, tuple([node_map[c] for c in child]))
            else: 
                new._add_triple(node_map[par], rel, node_map[child])    

        new.node_to_concepts = {}
        for node in self.node_to_concepts:
            if node in node_map:
                new.node_to_concepts[node_map[node]] = self.node_to_concepts[node]
            else: 
                new.node_to_concepts[node] = self.node_to_concepts[node]
        return new

    def apply_node_map(self, node_map, *args, **kwargs):
        new = Dag.apply_node_map(self, node_map, *args, **kwargs)    
        new.__class__ = Amr
        new.node_to_concepts = {} 
        for node in self.node_to_concepts:
            if node in node_map:
                new.node_to_concepts[node_map[node]] = self.node_to_concepts[node]
            else: 
                new.node_to_concepts[node] = self.node_to_concepts[node]
        return new
        
        
############################
# Pennman format AMR parser
############################

def ast_to_amr(ast):
    """
    Convert the abstract syntax tree returned by the amr parser into an amr.
    """
    dag = Amr()

    def rec_step(x):  # Closure over dag

        node, concept, roles = x         
        if type(node) is str:
            node = node.replace("@","")
            dag.node_to_concepts[node] = concept
            for role, child in roles:
                if type(child) == tuple and len(child) == 3:
                    childnode = child[0]                                           
                    if type(childnode) is str and childnode.startswith("@"):
                        childnode = childnode.replace("@","")
                        dag.external_nodes.append(childnode)
                    tuple_child = (childnode,)
                    dag[node].append(role, tuple_child)
                    x = dag[childnode]
                    rec_step(child)

                elif type(child) == list: #Hyperedge 
                    childnode = set()
                    for c in child: 
                        if type(c) == tuple and len(c) == 3:
                            if type(c[0]) is str and c[0].startswith("@"):
                                new_c = c[0].replace("@","")
                                dag.external_nodes.append(new_c)                               
                            else: 
                                new_c = c[0]
                            childnode.add(new_c)
                            rec_step(c)
                        else:
                            if type(c) is str and c.startswith("@"):
                                c = c.replace("@","")
                                dag.external_nodes.append(c)                               
                            childnode.add(c)
                    newchild = tuple(childnode)        
                    dag[node].append(role, newchild)
                    x = dag[newchild]

                else: # Just assume this node is some special symbol
                    if type(child) is str and child.startswith("@"):
                        child = child.replace("@","")
                        tuple_child = (child,)
                        dag.external_nodes.append(tuple_child)
                        dag[node].append(role, tuple_child)
                    else:
                        dag[node].append(role, (child,))
                    x = dag[child]

    root = ast[0]
    if type(root) == tuple and len(root) == 3: 
        dag.roots.append(root[0])
        rec_step(root)
    else: 
        dag.roots.append(root)

    return dag 



if __name__ == "__main__":
    amr = Amr.from_string("""(j / join-01
      :ARG0 (p / person :name (p2 / name :op1 "Pierre" :op2 "Vinken")
            :age (t / temporal-quantity :quant 61
                  :unit (y / year)))
      :ARG1 (b / board)
      :prep-as (d2 / director
            :mod (e / executive :polarity -))
      :time (d / date-entity :month 11 :day 29))""")
    #print amr
