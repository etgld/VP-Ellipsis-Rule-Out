import sys
import string
import re
import subprocess
from stanza.server import CoreNLPClient
from bllipparser import RerankingParser
from nltk.tree import Tree

rrp = RerankingParser.from_unified_model_dir('/home/e/.local/share/bllipparser/WSJ+Gigaword')  
client = CoreNLPClient(annotators=['parse'], timeout=30000, memory='8G')

# Not sure how many of these packages
# are necessary besides forest, landscape + geometry, and adjustbox
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

def stanford_parse(s):
    ann = client.annotate(s, output_format='json')
    return ann['sentences'][0]['parse']
    
def bllip_parse(s):
    return rrp.simple_parse(s)

def texify_tree(s):
    s_parse_tree = s.replace("(", "[")  
    s_parse_tree = s_parse_tree.replace(")", "]")
    s_parse_tree = s_parse_tree.replace("$", "\$")
    # Italicize leaves by convention
    s_parse_tree = re.sub(r'\s+(([A-Z]?[a-z]|[.,?]){1,})', r' [ \\textit{ \g<1> } ]', s_parse_tree)
    # This is specifically to deal with commas in the tree
    # which throw off forest (like a lot of things...)
    s_parse_tree = re.sub(r'\[(,)', r'[ \\textit{ \g<1> }', s_parse_tree)
    s_parse_tree = "\n \\begin{{forest}} \n\t{0}\n \\end{{forest}} \n".format(s_parse_tree)
    # adjustbox is what gets most of these to fit to the page (even in landscape)
    return "\n \\begin{{adjustbox}}{{max size={{\\textwidth}}{{\\textheight}}}} \n\t{0}\n \\end{{adjustbox}} \n".format(s_parse_tree)

def main():
    f_name = sys.argv[1]
    f = open(f_name, 'r')
    out_name = f_name.split('.')[0] + '.tex'
    out = open(out_name, 'w')
    count = 1
    out.write(head)
    for line in f:
        # This script takes a plain text file
        # with lines of the format <entry name>:<sentence>  
        temp = line.split(':')
        index = temp[0]
        text = temp[1]
        out.write("\n\n \\begin{samepage}")
        out.write("\n\n \\item  \\verb|{0}|  \n\n".format(index))
        out.write("\n\n {{\\it {0} }} \n\n".format(text.rstrip()))
        s_final = texify_tree(stanford_parse(text))
        b_final = texify_tree(bllip_parse(text))
        out.write("\\begin{itemize} \n\n \\item {\\bf Stanford Parser :} \n\n ")
        out.write(s_final)
        out.write("\n\n \\item {\\bf Charniak Parser: } \n\n") 
        out.write(b_final)
        out.write("\\end{itemize}")
        out.write("\n\n \\end{samepage}")
    out.write(tail)
    # this assumes you have LaTeX installed and working
    # with the pdflatex command
    # subprocess.run(['pdflatex', out_name])
    
if __name__ == "__main__":
    main()
