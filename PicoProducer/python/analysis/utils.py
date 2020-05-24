# Author: Izaak Neutelings (May 2020)
import os
import importlib
from TauFW.PicoProducer.tools.file import ensurefile
from TauFW.PicoProducer.tools.log import Logger
LOG = Logger('Analysis')

def ensuremodule(modname):
  """Check if module exists and has class of same name."""
  # TODO: absolute path
  modfile = ensurefile("python/analysis/%s.py"%(modname))
  modpath = "TauFW.PicoProducer.analysis.%s"%(modname) #modfile.replace('.py','').replace('/','.')
  try:
    module = importlib.import_module(modpath)
  except:
    LOG.throw(ImportError,"Importing module '%s' failed. Please check %s! cwd=%r"%(modfile,modfile,os.getcwd()))
  if not hasattr(module,modname):
    LOG.throw(IOError,"Module '%s' in %s does not have a module named '%s'!"%(module,modfile,modname))
  return module

def getmodule(modname):
  """Get give module from python module in python/analysis of the same name."""
  module = ensuremodule(modname)
  return getattr(module,modname)
