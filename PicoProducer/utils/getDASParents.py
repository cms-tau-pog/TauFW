#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Instructions:
#   utils/getDASParents.py /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17*/NANOAODSIM
from TauFW.common.tools.utils import unwraplistargs
from TauFW.common.tools.log import color
from TauFW.PicoProducer.storage.Sample import dasgoclient, LOG


def expanddas(*datasets,**kwargs):
  """Get full list of datasets for a list of DAS dataset patterns."""
  verbosity = kwargs.get('verb', 0)
  if verbosity>=1:
    print ">>> expanddas(%r)"%(datasets)
  datasets = unwraplistargs(datasets)
  for dataset in datasets[:]:
    if '*' not in dataset: continue
    index    = datasets.index(dataset)
    query    = "dataset=%s"%(dataset)
    if dataset.endswith('USER'):
      query += " instance=prod/phys03"
    subset   = dasgoclient(query,verb=verbosity).split('\n')
    datasets.remove(dataset)
    for i, subdataset in enumerate(subset):
      datasets.insert(index+1,subdataset)
  datasets.sort()
  return datasets
  

def getparent(dataset,depth=0,verb=0):
  """Recursively get full ancestory of DAS dataset."""
  if verb>=1:
    print ">>> getparent(%r)"%(dataset)
  query    = "parent dataset=%s"%(dataset)
  if dataset.endswith('USER'):
    query += " instance=prod/phys03"
  parent   = dasgoclient(query,verb=verb)
  parents  = [ ]
  if parent.count('/')==3:
    if depth<10: #and not (parent.replace('-','').endswith('GENSIM') or parent.endswith('RAW')):
      parents = getparent(parent,depth=depth+1,verb=verb) # recursive
    parents.append(parent)
  return parents
  

def addlineage(dataset,family,roots,depth=0,verb=0):
  """Recursively add lineage of DAS dataset to family tree.
  Stop if common ancestor is found in family tree."""
  if verb>=1:
    print ">>> addlineage(%r)"%(dataset)
  query    = "parent dataset=%s"%(dataset)
  if dataset.endswith('USER'):
    query += " instance=prod/phys03"
  parent   = dasgoclient(query,verb=verb)
  parents  = [ ]
  family.setdefault(dataset,[ ])
  if parent.count('/')==3 and depth<10:
    if parent in family: # found existing node; attach & stop recursion
      if dataset not in family[parent]:
        family[parent].append(dataset)
    else:
      kids = family.setdefault(parent,[ ]) # create new node
      kids.append(dataset)
      if dataset in roots:
        roots.remove(dataset) # is not common ancestor
      #if parent.replace('-','').endswith('GENSIM') or parent.endswith('RAW'):
      #  if parent not in roots:
      #    roots.append(parent) # common ancestor; stop recursion
      #else:
      addlineage(parent,family,roots,depth=depth+1,verb=verb) # recursive
  elif dataset not in roots:
    roots.append(dataset) # assume common ancestor & stop recursion
  

def printfamily(leaf,family,depth=0,mark=[ ],verb=0):
  """Recursively print family starting from common ancestor 'root'."""
  indent = ("  "*depth)
  line   = color(leaf) if leaf in mark else leaf
  print indent+line
  kids = family.get(leaf,None)
  if kids==None:
    print "Warning! %r not in family!"%(leaf)
  else:
    for kid in kids:
      printfamily(kid,family,depth=depth+1,mark=mark,verb=verb)
  

def main(args):
  simple    = False #args.simple
  verbosity = args.verbosity
  datasets  = expanddas(args.datasets,verb=verbosity)
  if simple:
    for dataset in datasets:
      parents = getparent(dataset,verb=verbosity)
      for i, parent in enumerate(parents):
        print ("  "*i)+parent
      print ("  "*(i+1))+dataset
  else:
    family = { }
    roots  = [ ]
    for dataset in datasets:
      addlineage(dataset,family,roots,verb=verbosity)
    for root in roots:
      printfamily(root,family,mark=datasets,verb=verbosity)
    #for dataset in datasets:
    #  lineage = getparent(dataset,verb=verbosity)
    #  lineage.append(dataset)
    #  root    = lineage[0]
    #  if root not in roots:
    #    roots.append(root) # common ancestor
    #  for i, leaf in enumerate(lineage,1):
    #    kids = family.setdefault(leaf,[ ]) # direct offspring
    #    if i<len(lineage) and lineage[i] not in kids:
    #      kids.append(lineage[i])
    #for root in roots[:]:
    #  if any(root in k for l, k in family.iteritems()):
    #    roots.remove(root) # not a common ancestor
    #    continue
    #  printfamily(root,family,mark=datasets,verb=verbosity)
  

if __name__ == '__main__':
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Trace & print parents of dataset."""
  parser = ArgumentParser(prog="getDASParents",description=description,epilog="Succes!")
  parser.add_argument('datasets',        nargs='+', default=[ ], action='store',
                      metavar="DATASET", help="dataset from DAS to trace & print" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  
