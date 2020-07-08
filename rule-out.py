import sys
import string
import re
import ast
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import Tree
from nltk.treeprettyprinter import TreePrettyPrinter

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

dominators = ['S', 'SBAR', 'SBARQ', 'SINV', 'SQ']

def listify_tree(s):
    s = s.replace('\n', '')
    s = s.replace("'", '')
    s = s.replace("(", "[")  
    s = s.replace(")", "]")
    s = re.sub(r"([\w\-?$]+[\.,]?)", r"'\g<1>'", s)
    s = re.sub(r'\[([\.,?])', r"['\g<1>'", s)
    s = re.sub(r'\s+([\.,?])', r" '\g<1>'", s)
    s = re.sub(r'(\])\s+', r"\g<1>, ", s)
    s = re.sub(r'([\'][\w\-?$]+[\.,]?[\'])\s+', r'\g<1>, ', s)
    s = re.sub(r'([\'][\.,?][\'])\s+', r'\g<1>, ', s)
    return ast.literal_eval(s)

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


    
