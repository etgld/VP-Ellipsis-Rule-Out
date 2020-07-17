import sys
import string
import re
import ast
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import Tree
from nltk.corpus import wordnet as wn
from nltk.treeprettyprinter import TreePrettyPrinter
from pattern.en import conjugate
from pattern.en import INFINITIVE, PRESENT, SG, SUBJUNCTIVE, PAST, PARTICIPLE


rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')


auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}
root_levels = {'ROOT', 'S1'}

def non_finite(v):
    return {conjugate(v, INFINITIVE),
            conjugate(v, PAST+PARTICIPLE),
            conjugate(v, PRESENT+PARTICIPLE)}

def is_non_finite(v):
    return v in non_finite(v)

def is_aux(v):
    return (v == 'MD') or (conjugate(v, INFINITIVE) in auxes) 

def is_non_aux(v):
    return v[:2] == 'VB'

# returns the nearest upper embedded clause 
def sup_embedded(ptree):
    if ptree.label() in root_levels.union(clause_levels)):
        if (ptree.parent().label() in root_levels.union(clause_levels)):
            return None
        else:
            return ptree
    else:
        sup_embedded(ptree.parent()) 

# returns the nearest lower embedded clause
def inf_embedded(ptree):
    if ptree.label() in root_levels.union(clause_levels)):
        for i, stree in enumerate(ptree):
            
def is_simple(ptree):
    isroot =  (ptree.label() == 'ROOT' or ptree.label() == 'S1') 
    no_embedded = all[(not contains_embedded(stree)) for i, stree in enumerate(ptree)]
    return isroot and no_embedded

def clause_overt_v_head(ptree):
    pass

def rule_out(ptree):
    pass

def list2ptree(s):
    return ParentedTree.fromstring(s)

def overt_not_aux(ptree):
    

def main():
    f_name = sys.argv[1]
    f = open(f_name, 'r')
    for line in f:
        temp = line.split(':')
        index = temp[0]
        text = temp[1]
        ann = client.annotate(text, output_format='json')
        s_parse_tree = ann['sentences'][0]['parse']
        s_final = list2ptree(s_parse_tree)
        b_parse_tree = rrp.simple_parse(text)
        b_final = list2ptree(b_parse_tree)
        print("index : {0} \n\n Stanford tree: \n {1} \n\n Charniak tree: \n {1}".format(index,
                                                                                         s_final,
                                                                                         b_final))
    
if __name__ == "__main__":
    main()


    
