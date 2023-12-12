#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
from past.builtins import basestring, unicode # for python2 compatibility
import os, sys, re, glob, json
from datetime import datetime
import importlib
import getpass, platform
from collections import OrderedDict
from TauFW.PicoProducer import basedir
from TauFW.common.tools.file import ensuredir, ensurefile
from TauFW.common.tools.log import Logger, color, bold, header


# DEFAULTS
LOG          = Logger('GLOB')
CONFIG       = None
user         = getpass.getuser()
host         = platform.node()
dtypes       = ['mc','data','embed']
sys.path.append(basedir)
_cfgdefaults = OrderedDict() # initiate once with getdefaultconfig


def getdefaultconfig(verb=0):
  """Get default configuration dictionary. Initiate if it does not exist yet."""
  global _cfgdefaults, basedir
  if _cfgdefaults: # initiate
    LOG.verb(">>> getdefaultconfig: _cfgdefaults already initiated",verb,level=3)
  else:
    LOG.verb(">>> getdefaultconfig: Initiating _cfgdefaults...",verb,level=3)
    from TauFW.PicoProducer.storage.utils import guess_sedir, guess_tmpdirs
    from TauFW.PicoProducer.batch.utils import guess_batch
    eras          = OrderedDict([
      ('2016','samples_2016.py'),
      ('2017','samples_2017.py'),
      ('2018','samples_2018.py')
    ])
    channels      = OrderedDict([
      ('skim','skimjob.py'),
      ('test','test.py'),
      ('mutau','ModuleMuTauSimple')
    ])
    sedir         = guess_sedir()                    # guess storage element on current host
    tmpskimdir, tmphadddir = guess_tmpdirs()         # tmphadddir: temporary dir for creating intermediate hadd files
                                                     # tmpskimdir: temporary dir for creating skimmed file before copying to outdir
    jobdir        = "output/$ERA/$CHANNEL/$SAMPLE"   # for job config and log files
    outdir        = tmphadddir+jobdir                # for job output
    picodir       = sedir+"analysis/$ERA/$GROUP"     # for storage of analysis ("pico") tuples after hadd
    nanodir       = sedir+"samples/nano/$ERA/$DAS"   # for storage of (skimmed) nanoAOD
    filelistdir   = "samples/files/$ERA/$SAMPLE.txt" # location to save list of files
    batchsystem   = guess_batch()                    # batch system (HTCondor, SLURM, ...)
    batchqueue    = ""                               # batch queue / job flavor
    batchopts     = ""                               # extra batch options
    nfilesperjob  = 1                                # group files per job
    maxevtsperjob = -1                               # maximum number of events per job (split large files)
    maxopenfiles  = 500                              # maximum number of open files during hadd
    ncores        = 4                                # number of cores for parallel event counting & validating of files
    haddcmd       = ""                               # alternative command for hadd'ing, e.g. 'python3 /.../.../haddnano.py'
    _cfgdefaults  = OrderedDict([                    # ordered dictionary with defaults
      ('channels',channels), ('eras',eras),
      #('basedir',basedir), # import instead
      ('jobdir',jobdir),     ('outdir',outdir), ('nanodir',nanodir), ('picodir',picodir),
      ('tmpskimdir',tmpskimdir),
      ('batch',batchsystem), ('queue',batchqueue), ('batchopts',batchopts),
      ('nfilesperjob',nfilesperjob), ('maxevtsperjob',maxevtsperjob),
      ('filelistdir',filelistdir),
      ('maxopenfiles',maxopenfiles), ('haddcmd', haddcmd ), # for pico.py hadd
      ('ncores',ncores),
    ])
  return _cfgdefaults
  

def getconfig(verb=0,refresh=False):
  """Get configuration from JSON file."""
  global basedir, CONFIG
  cfgdefaults = getdefaultconfig(verb=verb)
  if CONFIG and not refresh:
    return CONFIG
  
  # SETTING
  cfgdir   = ensuredir(basedir,"config")
  cfgname  = os.path.join(cfgdir,"config.json")
  bkpname  = os.path.join(cfgdir,"config.json.bkp") # back up to recover config if reset
  cfgdict  = cfgdefaults.copy()
  rqdstrs  = [k for k,v in cfgdefaults.items() if isinstance(v,basestring)] # required string type
  rqddicts = [k for k,v in cfgdefaults.items() if isinstance(v,dict)] # required dictionary type
  
  # GET CONFIG
  if os.path.isfile(cfgname):
    with open(cfgname,'r') as file:
      cfgdict = json.load(file,object_pairs_hook=OrderedDict)
    nmiss = len([0 for k in cfgdefaults.keys() if k not in cfgdict]) # count missing keys
    if nmiss>=5 and os.path.isfile(bkpname): # recover reset config file
      print(">>> Config file may have been reset. Opening backup %s..."%(bkpname))
      with open(bkpname,'r') as file:
        bkpcfgdict = json.load(file,object_pairs_hook=OrderedDict)
      for key in bkpcfgdict.keys(): # check for missing keys
        if key not in cfgdict:
          LOG.warning("Key '%s' not set in config file %s. Setting to backup %r"%(key,os.path.relpath(cfgname),bkpcfgdict[key]))
          cfgdict[key] = bkpcfgdict[key]
          nmiss += 1
    if nmiss>0:
      for key in cfgdefaults.keys(): # check for missing keys
        if key not in cfgdict:
          LOG.warning("Key '%s' not set in config file %s. Setting to default %r"%(key,os.path.relpath(cfgname),cfgdefaults[key]))
          cfgdict[key] = cfgdefaults[key]
          nmiss += 1
      print(">>> Saving updated keys...")
      with open(cfgname,'w') as file:
        json.dump(cfgdict,file,indent=2)
  else:
    LOG.warning("Config file '%s' does not exist in %s. Creating with defaults..."%(cfgname,cfgdir))
    with open(cfgname,'w') as file:
      json.dump(cfgdict,file,indent=2)
  
  # SANITY CHECKS - format of values for required keys
  for key in rqdstrs:
    assert key in cfgdict, "Required key '%s' not found in the configuration file..."%(key)
    assert isinstance(cfgdict[key],basestring),\
      "Required value for '%s' must be a string or unicode! Instead is of type %s: %r"%(key,type(cfgdict[key]),key)
  for key in rqddicts:
    assert key in cfgdict, "Required key '%s' not found in the configuration file..."%(key)
    assert isinstance(cfgdict[key],dict),\
      "Required value for '%s' must be a dictionary! Instead is of type %s: %r"%(key,type(cfgdict[key]),cfgdict[key])
  
  # RETURN
  if verb>=1:
    print('-'*80)
    print(">>> Reading config JSON file '%s'"%cfgname)
    for key, value in cfgdict.items():
      print(">>> %-13s = %s"%(key,value))
    print('-'*80)
  
  CONFIG = Config(cfgdict,cfgname)
  return CONFIG
  

def setdefaultconfig(verb=0):
  """Set configuration to default values."""
  global basedir, CONFIG
  cfgdefaults = getdefaultconfig(verb=verb)
  cfgdir  = ensuredir(basedir,"config")
  cfgname = os.path.join(cfgdir,"config.json")
  cfgdict = cfgdefaults.copy()
  if os.path.isfile(cfgname):
    LOG.warning("Config file '%s' already exists. Overwriting with defaults..."%(cfgname))
  CONFIG  = Config(cfgdict,cfgname)
  CONFIG.write(backup=False,verb=verb)
  return CONFIG
  

class Config(object):
  
  def __init__(self,cfgdict={ },path="config.json"):
    """Container class for a global configuration."""
    self._dict = cfgdict
    self._path    = path
    for key in list(self._dict.keys()):
      if isinstance(self._dict[key],unicode):
        self._dict[str(key)] = str(self._dict[key]) # convert unicode to str
      elif isinstance(self._dict[key],dict):
        for subkey in list(self._dict[key].keys()):
          item = self._dict[key][subkey]
          if isinstance(item,unicode):
            item = str(item)
          self._dict[str(key)].pop(subkey,None)
          self._dict[str(key)][str(subkey)] = item # convert unicode to str
      elif isinstance(key,unicode):
        self._dict[str(key)] = self._dict[key] # convert unicode to str
  
  def __str__(self):
    return str(self._dict)
  
  def __getattr__(self,key):
    if key in self.__dict__:
      val = self.__dict__[key]
    elif (key.startswith('__') and key.endswith('__')) or key not in self._dict:
      raise AttributeError("Did not find '%s'"%(key))
    else:
      val = self._dict[key]
    return val
  
  def __getitem__(self,key):
    return self._dict[key]
  
  def __setattr__(self,key,val):
    if key in self.__dict__:
      self.__dict__[key] = val
      if key in self._dict[key]:
        self._dict[key] = val
    elif (key.startswith('__') and key.endswith('__')):
      raise AttributeError("Did not find '%s'"%(key))
    elif key.startswith('_'):
      self.__dict__[key] = val
    else:
      self._dict[key] = val # cache
    return val
  
  def __setitem__(self,key,val):
    self._dict[key] = val
    return val
  
  def __iter__(self):
    return iter(self._dict)
  
  def iteritems(self):
    for x in self._dict.items():
      yield x
  
  def items(self):
    for x in self._dict.items():
      yield x
  
  def __len__(self):
    return len(self._dict)
  
  def __contains__(self, item):
    return item in self._dict
  
  def load(self,path=None):
    if path==None:
      path = self._path
    else:
      self._path = path
    with open(path,'r') as infile:
      self._dict = json.load(infile,object_pairs_hook=OrderedDict)
    return self._dict
  
  def keys(self,*args,**kwargs):
    return self._dict.keys(*args,**kwargs)
  
  def get(self,*args,**kwargs):
    return self._dict.get(*args,**kwargs)
  
  def pop(self,*args,**kwargs):
    return self._dict.pop(*args,**kwargs)
  
  def write(self,path=None,backup=False,verb=0):
    if path==None:
      path = self._path
    LOG.verb(">>> Config.write: Writing %r (backup=%r)"%(path,backup),verb,3)
    with open(path,'w') as outfile:
      json.dump(self._dict,outfile,indent=2)
    if backup: # backup to recover if config was reset
      pathbkp = path+'.bkp'
      LOG.verb(">>> Config.write: Making back up in %r"%(pathbkp),verb,2)
      with open(pathbkp,'w') as outfile:
        json.dump(self._dict,outfile,indent=2)
    return path
  
