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

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')


auxes = {'have', 'be', 'do', 'would', 'could',  'might'}
aux_level = 'MD'
clause_levels = {'S', 'SBAR', 'SBARQ', 'SINV', 'SQ'}

def non_finite(v):
    return conjugate(v, tense = "infinitive")

def is_aux(ptree):
    return ptree.label() == 'MD'

def is_non_aux(ptree):
    return ptree.label()[:2] == 'VB'

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
        s_final = listify_tree(s_parse_tree)
        b_parse_tree = rrp.simple_parse(text)
        b_final = listify_tree(b_parse_tree)
        print("index : {0} \n\n Stanford tree: \n {1} \n\n Charniak tree: \n {1}".format(index,
                                                                                         s_final,
                                                                                         b_final))
    
if __name__ == "__main__":
    main()


    
