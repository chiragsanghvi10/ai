import yaml
import os.path as path

def fetch_contant_single(contant_name):
    p = path.abspath(path.join(__file__ ,"../../../constants.yaml"))
    with open(p, 'r') as f:
        doc = yaml.load(f)
    return doc[contant_name]

def fetch_contant(parent, child):
    p = path.abspath(path.join(__file__ ,"../../../constants.yaml"))
    with open(p, 'r') as f:
        doc = yaml.load(f)
    return doc[parent][child]
