'''
Parse a feature-structure-style text encoding of an AMR.

@author: Daniel Bauer (dbauer)
@since: 2012-06-18
'''

from pyparsing import Literal,Word,CharsNotIn, OneOrMore, ZeroOrMore,Forward,nums,alphas, Optional 
from collections import defaultdict
import pyparsing
import unittest
import re
import sys
import copy


class StrLiteral(str):
        
    def __str__(self):
        return '"%s"' % "".join(self)

    def __repr__(self):
            return str(self)

class SpecialValue(str):
        pass


def make_amr_parser():
    """
    Pyparsing parser for AMRs. This will return an abstract syntax tree that
    needs to be converted into an AMR using ast_to_amr.
    """

    def parse_concept_expr(s, loc, tok):       
        node_name = tok[0]
        concept_name = None

        roles = []
        if len(tok) > 1:
           if type(tok[1]) is tuple:
                roles = tok[1:]
           else: 
              concept_name = tok[1]
              if len(tok) > 2:
                roles = tok[2:]
        return (node_name, concept_name, roles)
    
    parse_role = lambda s, loc, tok : (tok[0], tok[1:] if len(tok) > 2  else tok[1]) 

    # Number are all mapped to the same node in the graph because of interning
    parse_quantity = lambda s, loc, tok: float(tok[0]) if "." in tok[0] else int(tok[0]) 

    parse_string_literal = lambda s, loc, tok: StrLiteral(" ".join(tok)) 

    parse_special_value = lambda s, loc, tok: SpecialValue(" ".join(tok))

    lpar  = Literal( "(" ).suppress()
    rpar  = Literal( ")" ).suppress()

    quantity = Word(nums+".,").setParseAction(parse_quantity)

    node_name =  Word(alphas+nums+"_@")  

    concept_name = Word(alphas+nums+"-_")    
    role_name = Word(alphas+nums+":-_.$'&@") | Literal("#").suppress()+Word(alphas+nums+"[]-$_").setParseAction(lambda s, loc, tok: NonterminalEdge(tok[0]))     
    lit_string = Literal('"').suppress() + CharsNotIn('"') + Literal('"').suppress()

    expr = Forward()

    special_attr = Literal("-") | Literal("interrogative") | Literal("amr-unknown") # Extend list if neccessary


    value =  expr |\
             quantity.setParseAction(parse_quantity) |\
             special_attr.setParseAction(parse_special_value) | \
             node_name |\
             lit_string.setParseAction(parse_string_literal) 
  
    def debug(s, loc, tok):
        if len(tok) > 1:
            flat = [tok[0]] + tok[1:]
        else: 
            flat =  tok
        return flat

    valuelist = Forward()
    valuelist << (value + Literal(",").suppress() +valuelist | value).setParseAction(debug)
    role = (Literal(":").suppress() + role_name + valuelist).setParseAction(parse_role)

    expr.setParseAction(parse_concept_expr) 
    expr << (lpar +  node_name + Optional(Literal("/").suppress() + concept_name) + ZeroOrMore(role) + rpar)
    
    return expr 

