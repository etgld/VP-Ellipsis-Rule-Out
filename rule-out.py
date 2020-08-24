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

from copy import deepcopy

# Tests for embedded clause functions
test1 = "He wouldn't make the rice if it had already been made."
test2 = "The first plumber, who arrived before three, and the second plumber, who arrived after four, both said the pipe was clogged."
test3 = "The doctor who talked to us said the swelling would probably be gone after two days."
tests = {test1, test2, test3}

auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}
root_levels = {'ROOT', 'S1'}
punct = {'.', '.', '?'}

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

modal_aux_ts = set(open('modal_aux_triggers').read().split())
have_ts = set(open('have_triggers').read().split())
be_ts = set(open('be_triggers').read().split())
do_ts = set(open('do_triggers').read().split())
to_ts = set(open('to_triggers').read().split())
not_ts = set('not')
non_standard_ts = set(open('non-standard_triggers').read().split())
triggers = modal_aux_ts.union(have_ts, be_ts, do_ts, to_ts, not_ts)

# unfortunately the ParentedTree data structure
# treats leaves as just strings
# without labels or parents.
# This workaround adapted from https://stackoverflow.com/a/25972853
# potential issues if there are multiple instances of the same trigger
def leaf_parent(ptree, l):
    leaves = ptree.leaves()
    leaf_idx = leaves.index(l)
    tree_loc = ptree.leaf_treeposition(leaf_idx)
    parent_loc = tree_loc[:-1]
    return ptree[parent_loc]

def possible_trigger_sites(ptree):
    leaves = ptree.leaves()
    sites = []
    for leaf in leaves:
        if leaf in triggers:
            # sites.append(leaf_parent(ptree, leaf))
            sites.append(leaf_parent(ptree, leaf).parent())
    return sites
                
def stanford_parse(s):
    ann = client.annotate(s, output_format='json')
    return ann['sentences'][0]['parse']
    
def bllip_parse(s):
    return rrp.simple_parse(s)


# stree1 precedes stree2 in ptree if stree1 is to the left
# of stree2 in ptree and stree1 is not a subtree of stree2
def precedes(stree1, stree2):
    t1 = stree1.treeposition()
    t2 = stree2.treeposition()
    # tree positions are represented via tuples
    # containing the indices of their ancestors with respect to
    # previous ancestor starting from the root and going down
    least = min(len(t1), len(t2))
    # using <= since we need to allow 
    # for the anaphora site being contained in the same VP
    # as the elided content as in the 'antecedent-contained'
    # examples in basic-VPE
    return t1[:least] <= t2[:least]

def is_clause_VP(ptree):
    return ptree.label() == 'VP' and ptree.parent().label() != 'VP'

def preceding_VPs(main_tree, trigger_site):
    return main_tree.subtrees(filter = lambda x : is_clause_VP(x) and precedes(x, trigger_site))

# This guards against multiple identical
# subtrees appearing in the full tree barring
# some bizarre literary case like
# "We saw the cars go by and we saw the cars go by"
def peq(p1, p2):
    teq = p1 == p2
    # might be redundant -- need to check
    place_eq = p1.parent() == p2.parent()
    return teq and place_eq

# returns list of immediate children of a ParentedTree
def children(ptree):
    return [stree for stree in ptree]

# returns list of immediate children of a ParentedTree with a certain label
def find_childen(ptree, label):
    return [stree for stree in ptree if stree.label() == label]

# return given main tree without the instance
# of the given subtrees - using peq to avoid deletion
# of otherwise identical subtrees
def tree_minus(main_tree, sub_trees):
    # using deep-copy since non-naive/destructive editing is tricky for nltk trees
    result = deepcopy(main_tree) 
    for stree in result.subtrees(filter = lambda x : any([peq(x, stree) for stree in sub_trees])):
        s_parent = stree.parent()
        s_idx = s_parent.index(stree)
        s_parent.__delitem__(s_idx)
    return result

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

def possible_v_head(v):
    return v.label()[:2] == 'VB'

# For this we only care
# about the tag since calling the
# pattern library can add time
def is_verb(v):
    return (v.label() == 'MD') or possible_v_head(v)

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

# requirement to be a valid case of VPE
def clause_elided_non_finite(ptree):
    v_head = clause_overt_v_head(ptree)
    return is_non_finite(v_head) and not is_aux(v_head)

def list2ptree(s):
    return ParentedTree.fromstring(s)

def main():
    if len(sys.argv) > 1:
        f = open(sys.argv[1], 'r')
        sentences = [line.split(':')[1] for line in f]
        print(sentences)
    else:
        sentences = tests
    for test in sentences:
        s_parse_tree = stanford_parse(test)
        s_final = list2ptree(s_parse_tree)
        print(test)
        print("VERB: {0}".format(clause_overt_v_head(s_final)))
        pts = possible_trigger_sites(s_final)
        #preceding_trigger = tree_minus(s_final, pts)
        preceding_trigger = preceding_VPs(s_final, pts[0])
        print("####### ORIGINAL #######")
        s_final.pretty_print()
        print("####### PRECEDING_TRIGGER #######")
        #preceding_trigger.pretty_print()
        count = 0
        #for site in pts:
        for vp in preceding_trigger:
            print("### SITE {0} ###".format(count))
            vp.pretty_print()
            print(vp.treeposition())
            count += 1
        
if __name__ == "__main__":
    main()
    
