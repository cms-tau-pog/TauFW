# Author: Izaak Neutelings (May 2020)
import os, sys
import traceback
import importlib
from TauFW.PicoProducer import basedir
from TauFW.PicoProducer.tools.file import ensurefile
from TauFW.PicoProducer.tools.log import Logger
LOG = Logger('Analysis')


def ensuremodule(modname):
  """Check if module exists and has class of same name."""
  # TODO: absolute path
  modfile = ensurefile(basedir,"python/analysis/%s.py"%(modname))
  modpath = "TauFW.PicoProducer.analysis.%s"%(modname) #modfile.replace('.py','').replace('/','.')
  try:
    module = importlib.import_module(modpath)
  except Exception as err:
    print traceback.format_exc()
    LOG.throw(ImportError,"Importing module '%s' failed. Please check %s! cwd=%r"%(modpath,modfile,os.getcwd()))
  if not hasattr(module,modname):
    LOG.throw(IOError,"Module '%s' in %s does not have a module named '%s'!"%(module,modfile,modname))
  return module
  

def getmodule(modname):
  """Get give module from python module in python/analysis of the same name."""
  module = ensuremodule(modname)
  return getattr(module,modname)
  

def dumpgenpart(part,genparts=None,event=None):
  """Print information on gen particle. If collection is given, also print mother's PDG ID."""
  info = ">>>  i=%2s, PID=%3s, status=%2s, mother=%2s"%(part._index,part.pdgId,part.status,part.genPartIdxMother)
  if part.genPartIdxMother>=0:
    if genparts: 
      moth  = genparts[part.genPartIdxMother].pdgId
      info += " (%s)"%(moth)
    elif event:
      moth  = event.GenPart_pdgId[part.genPartIdxMother]
      info += " (%s)"%(moth)
  print info
  
