#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os, sys, re, glob, json
from datetime import datetime
import importlib
import getpass, platform
from collections import OrderedDict
from TauFW.PicoProducer import basedir
from TauFW.common.tools.file import ensuredir, ensurefile
from TauFW.common.tools.log import Logger, color, bold, header
from TauFW.PicoProducer.storage.utils import getsedir, gettmpdirs


# DEFAULTS
LOG            = Logger('GLOB')
CONFIG         = None
user           = getpass.getuser()
host           = platform.node()
#basedir       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
dtypes         = ['mc','data','embed']
_eras          = OrderedDict([
  ('2016','samples_2016.py'),
  ('2017','samples_2017.py'),
  ('2018','samples_2018.py')
])
_channels      = OrderedDict([
  ('skim','skimjob.py'),
  ('test','test.py'),
  ('mutau','ModuleMuTauSimple')
])
_sedir         = getsedir()                       # guess storage element on current host
_tmpskimdir, _tmphadddir = gettmpdirs()           # _tmphadddir: temporary dir for creating intermediate hadd files
                                                  # _tmpskimdir: temporary dir for creating skimmed file before copying to outdir
_jobdir        = "output/$ERA/$CHANNEL/$SAMPLE"   # for job config and log files
_outdir        = _tmphadddir+_jobdir              # for job output
_picodir       = _sedir+"analysis/$ERA/$GROUP"    # for storage of analysis ("pico") tuples after hadd
_nanodir       = _sedir+"samples/nano/$ERA/$DAS"  # for storage of (skimmed) nanoAOD
_filelistdir   = "samples/files/$ERA/$SAMPLE.txt" # location to save list of files
_batchsystem   = 'HTCondor'                       # batch system (HTCondor, SLURM, ...)
_queue         = ""                               # batch queue / job flavor
_nfilesperjob  = 1                                # group files per job
_maxevtsperjob = -1                               # maximum number of events per job (split large files)
_maxopenfiles  = 500                              # maximum number of open files during hadd
_ncores        = 4                                # number of cores for parallel event counting & validating of files
_cfgdefaults   = OrderedDict([                    # ordered dictionary with defaults
  ('channels',_channels), ('eras',_eras),
  ('basedir',basedir),
  ('jobdir',_jobdir),     ('outdir',_outdir), ('nanodir',_nanodir), ('picodir',_picodir),
  ('tmpskimdir',_tmpskimdir),
  ('batch',_batchsystem), ('queue',_queue),
  ('nfilesperjob',_nfilesperjob), ('maxevtsperjob',_maxevtsperjob),
  ('filelistdir',_filelistdir),
  ('maxopenfiles',_maxopenfiles),
  ('ncores',_ncores),
])
sys.path.append(basedir)


def getconfig(verb=0,refresh=False):
  """Get configuration from JSON file."""
  global _cfgdefaults, basedir, CONFIG
  if CONFIG and not refresh:
    return CONFIG
  
  # SETTING
  cfgdir   = ensuredir(basedir,"config")
  cfgname  = os.path.join(cfgdir,"config.json")
  cfgdict  = _cfgdefaults.copy()
  rqdstrs  = [k for k,v in _cfgdefaults.iteritems() if isinstance(v,basestring)]
  rqddicts = [k for k,v in _cfgdefaults.iteritems() if isinstance(v,dict)]
  
  # GET CONFIG
  if os.path.isfile(cfgname):
    with open(cfgname,'r') as file:
      cfgdict = json.load(file,object_pairs_hook=OrderedDict)
    update = False
    for key in _cfgdefaults.keys(): # check for missing keys
      if key not in cfgdict:
        LOG.warning("Key '%s' not set in config file %s. Setting to default %r"%(key,os.path.relpath(cfgname),_cfgdefaults[key]))
        cfgdict[key] = _cfgdefaults[key]
        update = True
    if update:
      print ">>> Saving defaults..."
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
    print '-'*80
    print ">>> Reading config JSON file '%s'"%cfgname
    for key, value in cfgdict.iteritems():
      print ">>> %-13s = %s"%(key,value)
    print '-'*80
  
  CONFIG = Config(cfgdict,cfgname)
  return CONFIG


def setdefaultconfig(verb=0):
  """Set configuration to default values."""
  global _cfgdefaults, basedir, CONFIG
  
  # SETTING
  cfgdir  = ensuredir(basedir,"config")
  cfgname = os.path.join(cfgdir,"config.json")
  cfgdict = _cfgdefaults.copy()
  if os.path.isfile(cfgname):
    LOG.warning("Config file '%s' already exists. Overwriting with defaults..."%(cfgname))
  CONFIG  = Config(cfgdict,cfgname)
  CONFIG.write()
  return CONFIG
  

class Config(object):
  
  def __init__(self,cfgdict={ },path="config.json"):
    """Container class for a global configuration."""
    self._dict = cfgdict
    self._path    = path
    for key in self._dict.keys():
      if isinstance(self._dict[key],unicode):
        self._dict[str(key)] = str(self._dict[key]) # convert unicode to str
      elif isinstance(self._dict[key],dict):
        for subkey in self._dict[key].keys():
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
    for x in self._dict.iteritems():
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
  
  def write(self,path=None):
    if path==None:
      path = self._path
    with open(path,'w') as outfile:
      json.dump(self._dict,outfile,indent=2)
    return path
  
