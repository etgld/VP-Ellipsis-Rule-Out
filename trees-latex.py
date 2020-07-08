import sys
import string
import re
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import Tree
from nltk.treeprettyprinter import TreePrettyPrinter

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

head = """\\documentclass[landscape, 12pt]{article} 
\\usepackage{amsfonts}
\\usepackage{amstext}
\\usepackage{amsmath}
\\usepackage{fancyhdr}
\\usepackage{amsthm}
\\usepackage{epsfig}
\\usepackage{graphicx}
\\usepackage{multicol}
\\usepackage{tikz}
\\usepackage{amssymb}
\\usepackage[all]{xy}
\\usepackage{enumitem}
\\usepackage{forest}
\\usepackage{adjustbox}
\\usepackage[landscape]{geometry}
\\usetikzlibrary{automata, positioning, shapes, arrows}

\\begin{document}
\\begin{enumerate}"""

tail = """\\end{enumerate}
\\end{document}"""

def texify_tree(s):
    s_parse_tree = s.replace("(", "[")  
    s_parse_tree = s_parse_tree.replace(")", "]")
    s_parse_tree = s_parse_tree.replace("$", "\$")
    s_parse_tree = re.sub(r'\s+(([A-Z]?[a-z]|[.,?]){1,})', r' [ \\textit{ \g<1> } ]', s_parse_tree)
    s_parse_tree = re.sub(r'\[(,)', r'[ \\textit{ \g<1> }', s_parse_tree)
    s_parse_tree = "\n \\begin{{forest}} \n{0}\n \\end{{forest}} \n".format(s_parse_tree)
    return "\n \\begin{{adjustbox}}{{max size={{\\textwidth}}{{\\textheight}}}} \n{0}\n \\end{{adjustbox}} \n".format(s_parse_tree)

def main():
    f_name = sys.argv[1]
    f = open(f_name, 'r')
    out_name = 'Result_Trees.tex'
    out = open(out_name, 'w')
    count = 1
    out.write(head)
    for line in f:
        temp = line.split(':')
        index = temp[0]
        text = temp[1]
        out.write("\\begin{samepage}")
        out.write("\n\n \\item  \\verb|{0}|  \n\n".format(index))
        out.write("\n\n {{\\it {0} }} \n\n".format(text.rstrip()))
        ann = client.annotate(text, output_format='json')
        s_parse_tree = ann['sentences'][0]['parse']
        s_final = texify_tree(s_parse_tree)
        b_parse_tree = rrp.simple_parse(text)
        b_final = texify_tree(b_parse_tree)
        out.write("\\begin{itemize} \n\n \\item {\\bf Stanford Parser :} \n\n ")
        out.write(s_final)
        out.write("\n\n \\item {\\bf Charniak Parser: } \n\n") 
        out.write(b_final)
        out.write("\\end{itemize}")
        out.write("\\end{samepage}")
    out.write(tail)
    
if __name__ == "__main__":
    main()
