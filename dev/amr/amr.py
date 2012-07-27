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
                        new_amr.replace_triple(par, rel, child, par, part1, child)
                    new_amr.node_to_concepts[child] = part2
                if part1.lower() == "root":
                    new_amr.roots.remove(par)
                    new_amr.remove_triple(par, rel, child)
                    new_amr.roots.append(child)
        return new_amr

    def to_concept_edge_labels(self):
        """"
        Return an new DAG with equivalent structure as this AMR (plus additional root-edge), in
        which concepts are pushed into incoming edges.
        """

        new_amr = clone_as_dag()
        for par, rel, child in self.triples(instances = False):
            if child in self.node_to_concepts:
                new_rel = "%s:%s" % (rel, self.node_to_concepts[child])
                new_amr._replace_triple(par,rel,child, par, new_rel, child)
        for r in self.roots:
            count = 0
            if r in self.node_to_concepts:
                new_rel = "root:%s" % self.node_to_concepts[r]
            else: 
                new_rel = "root"
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
        for p,r,c in self.triples(instances = False):
            p_new = str(p)
            c_new = str(c)
            new_amr.add_triple(p_new, r, c_new)

        new_amr.roots = [str(r) for r in self.roots]
        for node in self.node_to_concepts:    
            new_amr.set_concept(str(node), self.node_to_concepts[node])
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
        
############################
# Pennman format AMR parser
############################

def ast_to_amr(ast):
    """
    Convert the abstract syntax tree returned by the amr parser into an amr.
    """
    amr = Amr()

    def rec_step(x):  # Closure over amr

            node, concept, roles = x         
            if type(node) is str:
                node = node.replace("@","")
            amr.node_to_concepts[node] = concept

            for role, child in roles:

                # Flip inverse -OF edges
                #if r.upper().endswith("-OF"): #Check for inverse edges
                #    new_rel = r[:-3] #Rename location
                #    if type(child) == str: 
                #        graph[child].append((new_rel, node))
                #    else: 
                #        childnode = child[0]
                #        graph[childnode].append((new_rel, node))
                #        if not childnode in roots:
                #            roots.append(childnode)
                #        rec_step(child)
                #else: 

   
                if type(child) == tuple and len(child) == 3:
                    childnode = child[0]                                           
                    if type(childnode) is str and childnode.startswith("@"):
                        childnode = childnode.replace("@","")
                        amr.external_nodes.add(childnode)                               
                    amr[node].append(role, childnode)
                    x = amr[childnode]
                    rec_step(child)

                elif type(child) == list: #Hyperedge
                    childnode = set()
                    for c in child: 
                        if type(c) == tuple and len(c) == 3:
                            if type(child) is str and c[0].startswith("@"):
                                c[0] = c[0].replace("@","")
                                amr.external_nodes.add(c[0])                               
                            childnode.add(c[0])
                            rec_step(c)
                        else:
                            if type(c) is str and c.startswith("@"):
                                c = c.replace("@","")
                                amr.external_nodes.add(c)                               
                            childnode.add(c)
                    newchild = tuple(childnode)        
                    amr[node].append(role, newchild)
                    x = amr[newchild]

                else: # Just assume this node is some special symbol
                    if type(child) is str and child.startswith("@"):
                        child = child.replace("@","")
                        amr.external_nodes.add(child)
                        amr[node].append(role, child)
                    else:
                        amr[node].append(role, child)

    root = ast[0]
    if type(root) == tuple and len(root) == 3: 
        amr.roots.append(root[0])
        rec_step(root)
    else: 
        amr.roots.append(root)

    return amr 


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
