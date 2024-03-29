# Setup Instructions
  - Install `conda` or if installed run `conda update -n base -c defaults conda`
  - Run `conda create -n VPE python=3.6` (Pattern (used for verb conjugation) and the BLLIP Parser don't support later versions of python).   
  - Run `conda activate VPE`           
  - Run `conda install nltk pip`
  - Run `conda install -c stanfordnlp stanza`     
  - Follow the instructions for installing the Stanford CoreNLP suite as instructed here https://github.com/stanfordnlp/stanza#accessing-java-stanford-corenlp-software
  - This might be unecessary but run `python -m pip install --upgrade pip` 
  - Run `pip install bllipparser pattern` 
  - Run `python -mbllipparser.ModelFetcher -l` to see the list of available models for the BLLIP Parser.    
  - Run `python -mbllipparser.ModelFetcher -i <Model Name>` to install a particular model (currently the code uses =WSJ+Gigaword=).
  - You will have to alter `rule-out.py` and `trees-latex.py` to reflect the path where you have installed the model. In the case of my Linux machine the path is `/home/<username>/.local/share/bllipparser/`   
  - For Windows, building `bllipparser` is trickier, a list of builds for Windows are available here https://github.com/BLLIP/bllip-parser#other-versions-of-the-parser  
