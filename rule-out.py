import sys
import string
import re
import ast
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import ParentedTree
from pattern.en import conjugate
from pattern.en import INFINITIVE, PRESENT, SG, SUBJUNCTIVE, PAST, PARTICIPLE


rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')


auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}
root_levels = {'ROOT', 'S1'}
punct = {'.', '.', '?'}

# This guards against multiple identical
# subtrees appearing in the full tree barring
# some bizarre literary case like
# "We saw the cars go by and we saw the cars go by"
def peq(p1, p2):
    teq = p1 == p2
    place_eq = p1.parent() == p2.parent()
    return teq and place_eq

def children(ptree):
    return [stree for stree in ptree]

def non_finite(v):
    return {conjugate(v, INFINITIVE),
            conjugate(v, PAST+PARTICIPLE),
            conjugate(v, PRESENT+PARTICIPLE)}

def is_non_finite(v):
    return v in non_finite(v)

def is_aux(v):
    return (v.label() == 'MD') or (conjugate(children(v)[0], INFINITIVE) in auxes) 

def is_non_aux(v):
    return v.label()[:2] == 'VB'

# returns the nearest upper embedded clause
# (determines if the immediate clause is embedded) 
def sup_embedded(ptree):
    if ptree.label() in root_levels.union(clause_levels)):
        # this happens often with coordinated conjunctions and does not
        # constitute embedding
        if (ptree.parent().label() in root_levels.union(clause_levels)):
            return None
        else:
            return ptree
    else:
        sup_embedded(ptree.parent()) 

# returns the nearest lower embedded clauses
def inf_embedded(ptree, embedded = []):
    if children(ptree) == ptree.leaves():
        return None
    if ptree.label() not in root_levels.union(clause_levels)):
        for stree in ptree:
            if stree.label() in clause_levels:
                embedded.append(stree)
            else:
                inf_embedded(stree, embedded)
    return embedded

def is_simple(ptree): 
    return all[(not contains_embedded(stree)) for stree in ptree.root()]

def clause_overt_v_head(ptree):
    head_tag = children(ptree)[0]
    if ptree.label() == 'VP':
        
            

def rule_out(ptree):
    pass

def list2ptree(s):
    return ParentedTree.fromstring(s)

def overt_not_aux(ptree):
    

def main():
    pass

if __name__ == "__main__":
    main()


    
