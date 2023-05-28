# Author: Izaak Neutelings (May 2020)
import os
from TauFW.common.tools.utils import unwraplistargs, execute, CalledProcessError
from TauFW.PicoProducer.storage.utils import LOG


def dasgoclient(query,**kwargs):
  """Help function to call dasgoclient and retrieve data set information."""
  try:
    verbosity = kwargs.get('verb',     0  )
    instance  = kwargs.get('instance', "" )
    limit     = kwargs.get('limit',    0  )
    option    = kwargs.get('opts',     "" )
    if instance:
      query  += " instance=%s"%(instance)
    dascmd    = 'dasgoclient --query="%s"'%(query)
    if limit>0:
      dascmd += " --limit=%d"%(limit)
    if option:
      dascmd += " "+option.strip()
    LOG.verb(repr(dascmd),verbosity)
    cmdout    = execute(dascmd,verb=verbosity-1)
  except CalledProcessError as e:
    print
    LOG.error("Failed to call 'dasgoclient' command. Please make sure:\n"
              "  1) 'dasgoclient' command exists.\n"
              "  2) You have a valid VOMS proxy. Use 'voms-proxy-init -voms cms -valid 200:0' or 'source utils/setupVOMS.sh'.\n"
              "  3) The DAS dataset in '%s' exists!\n"%(dascmd))
    raise e
  return cmdout
  

def getdasfiles(daspath,**kwargs):
  """Get files."""
  dascmd = "file dataset=%s"%(daspath)
  cmdout = dasgoclient(dascmd,**kwargs)
  outlist = cmdout.split(os.linesep)
  return outlist
  

def getdasnevents(daspath,**kwargs):
  """Get number of events."""
  dascmd = "summary dataset=%s"%(daspath)
  cmdout = dasgoclient(dascmd,**kwargs)
  if "nevents" in cmdout:
    nevts = int(cmdout.split('"nevents":')[1].split(',')[0])
  else:
    nevts = 0
    LOG.warning("getdasnevents: Could not get number of events from DAS for %r."%(daspath))
  return nevts
  

def expanddas(*datasets,**kwargs):
  """Get full list of datasets for a list of DAS dataset patterns."""
  verbosity = kwargs.get('verb', 0)
  if verbosity>=1:
    print(">>> expanddas(%r)"%(datasets))
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
    print(">>> getparent(%r)"%(dataset))
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
  
