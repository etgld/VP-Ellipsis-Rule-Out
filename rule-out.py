import sys
import string
import re
import ast
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import ParentedTree
from nltk.treeprettyprinter import TreePrettyPrinter
from pattern.en import conjugate
from pattern.en import INFINITIVE, PRESENT, SG, SUBJUNCTIVE, PAST, PARTICIPLE

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

# Tests for embedded clause functions
test1 = "He wouldn't make the rice if it had already been made."
test2 = "The first plumber, who arrived before three, and the second plumber, who arrived after four, both said the pipe was clogged."
test3 = "The doctor who talked to us said the swelling would probably be gone after two days."
tests = {test1, test2, test3}

auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}
root_levels = {'ROOT', 'S1'}
punct = {'.', '.', '?'}

def stanford_parse(s):
    ann = client.annotate(s, output_format='json')
    return ann['sentences'][0]['parse']
    
def bllip_parse(s):
    return rrp.simple_parse(s)

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

def find_childen(ptree, label):
    return [stree for stree in ptree if stree.label() == label]

# for a given verb return it's non-finite forms
# since in any case of VPE in English
# the elided VP must be non-finite
def non_finite(v):
    return {conjugate(v, INFINITIVE),
            conjugate(v, PAST+PARTICIPLE),
            conjugate(v, PRESENT+PARTICIPLE)}

def is_non_finite(v):
    return v in non_finite(v)

# Not all auxes get tagged with MD
# e.g. 'The drain was clogged' thus the
# manual check in the list of bare form auxes
def is_aux(v):
    return (v.label() == 'MD') or (conjugate(children(v)[0], INFINITIVE) in auxes) 

def is_non_aux(v):
    return v.label()[:2] == 'VB'

# For this we only care
# about the tag since calling the
# pattern library can add time
def is_verb(v):
    return (v.label() == 'MD') or is_non_aux(v)

# returns the nearest upper embedded clause
# (determines if the immediate clause is embedded) 
def sup_embedded(ptree):
    if ptree.label() in root_levels.union(clause_levels):
        # this happens often with coordinating conjunctions and does not
        # constitute embedding
        if (ptree.parent().label() in root_levels.union(clause_levels)):
            return None
        # If we have a clause with a none clause parent that's what we want
        else:
            return ptree    
    else:
        sup_embedded(ptree.parent()) 

# returns the nearest lower embedded clauses
def inf_embedded(ptree, embedded):
    # If at the end of the tree then there's nothing
    if children(ptree) == ptree.leaves():
        return None
    # No clause child of a root node counts as embedded
    elif ptree.label() in root_levels:
        for stree in ptree:
            if stree.label() in clause_levels:
                inf_embedded(stree, embedded)
    # likewise for clause children of clause nodes
    # since this is how taggers deal with
    # coordinating conjunctions
    elif ptree.label() in clause_levels:
        for stree in ptree:
            if stree.label() not in clause_levels:
                inf_embedded(stree, embedded)
    elif ptree.label() not in root_levels.union(clause_levels):
        for stree in ptree:
            # clause children of non-clause/root nodes are what we want
            if stree.label() in clause_levels:
                embedded.append(stree)
            # otherwise keep looking
            else:
                inf_embedded(stree, embedded)        
    return embedded

def clause_overt_v_head(ptree):
    # If there's a coordinating conjunction
    # look in the first clause (as a convention)
    if ptree.label() in root_levels:
        return clause_overt_v_head(children(ptree)[0]) 
    elif ptree.label() in clause_levels:
        for stree in ptree:
            # The priority is to find the main VP so look
            # for that first
            if stree.label() == 'VP':
                return clause_overt_v_head(stree)
            # If no VP is found look in any children 
            # which are clauses
            elif stree.label() in clause_levels:
                return clause_overt_v_head(stree)
    elif ptree.label() == 'VP':
        vps = find_childen(ptree, 'VP')
        # If the VP is nested look for the 
        # terminal leftmost VP
        if vps:
            return clause_overt_v_head(vps[0])
        # If at the terminal VP 
        # filter for the unique verb
        else: 
           for stree in ptree:
               if is_verb(stree):
                   return stree

# Test if a sentence or clause is simple
# by seeing if it has any embedded clasuses
def is_simple(ptree): 
    return all([(not inf_embedded(stree)) for stree in ptree.root()])

def rule_out(ptree):
    pass

def list2ptree(s):
    return ParentedTree.fromstring(s)

def overt_not_aux(ptree):
    return not is_aux(clause_overt_v_head(ptree)) 

def main():
    f_name = sys.argv[1]
    if f_name:
        f = open(f_name, 'r')
        sentences = [line.split(':')[1] for line in f]
        print(sentences)
    else:
        sentences = tests
    for test in sentences:
        s_parse_tree = stanford_parse(test)
        s_final = list2ptree(s_parse_tree)
        print(test)
        s_final.pretty_print()
        print("VERB: {0}".format(clause_overt_v_head(s_final)))
        #for elem in inf_embedded(s_final, []):
        #    elem.pretty_print()
        
if __name__ == "__main__":
    main()
    
