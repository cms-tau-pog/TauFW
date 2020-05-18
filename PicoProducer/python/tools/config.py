#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
import os, sys, re, glob, json
from datetime import datetime
import importlib
from collections import OrderedDict
from TauFW.PicoProducer.tools.file import ensuredir, ensurefile
from TauFW.PicoProducer.tools.log import Logger, color, bold, header
from TauFW.PicoProducer.storage.Storage import getsedir
LOG = Logger('GLOB')

# DEFAULTS
_basedir      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
_eras         = { '2016': 'samples_2016.py', '2017': 'samples_2017.py' }
_channels     = { 'test': 'test.py', } # TODO: load from config
_batchsystem  = 'HTCondor'
_dtypes       = ['mc','data','embed']
_sedir        = getsedir()                      # guess storage element on current host
_tmpdir       = "$TMPDIR"                       # temporary dir for creating intermediate hadd files
_jobdir       = "output/$ERA/$CHANNEL/$SAMPLE"  # for job config and log files
_outdir       = _sedir+_jobdir                  # for job output
_picodir      = _sedir+"analysis/$ERA/$GROUP"   # for storage of analysis ("pico") tuples after hadd
_nanodir      = _sedir+"samples/nano/$ERA/$DAS" # for storage of (skimmed) nanoAOD
_nfilesperjob = 1
_cfgdefaults  = OrderedDict([
  ('basedir',_basedir),
  ('jobdir',_jobdir),     ('outdir',_outdir), ('nanodir',_nanodir), ('picodir',_picodir),
  ('channels',_channels), ('eras',_eras),
  ('batch',_batchsystem), ('nfilesperjob',_nfilesperjob),
])
sys.path.append(_basedir)
os.chdir(_basedir)



def getconfig(verb=0):
  """Get configuration from JSON file."""
  global _cfgdefaults, _basedir
  
  # SETTING
  cfgdir   = ensuredir(_basedir,"config")
  cfgname  = os.path.join(cfgdir,"config.json")
  cfgdict  = _cfgdefaults.copy()
  rqdstrs  = [k for k,v in _cfgdefaults.iteritems() if isinstance(v,str)]
  rqddicts = [k for k,v in _cfgdefaults.iteritems() if isinstance(v,dict)]
  
  # GET CONFIG
  if os.path.isfile(cfgname):
    with open(cfgname,'r') as file:
      cfgdict = json.load(file,object_pairs_hook=OrderedDict)
    update = False
    for key in _cfgdefaults.keys(): # check for missing keys
      if key not in cfgdict:
        LOG.warning("Key '%s' not set in config file %s. Setting to default %r"%(key,cfgname,_cfgdefaults[key]))
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
    assert key in rqdstrs, "Required key '%s' not found in the configuration file..."%(key)
    assert isinstance(cfgdict[key],str) or isinstance(cfgdict[key],unicode),\
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
  
  config = Config(cfgdict,cfgname)
  return config
  


class Config(object):
  
  def __init__(self,cfgdict={ },path="config.json"):
    """Container class for a global configuration."""
    self._dict = cfgdict
    self._path    = path
  
  def __str__(self):
    return str(self._dict)
  
  def __getattr__(self,key):
    if key in self.__dict__:
      val = self.__dict__[key]
    elif (key.startswith('__') and key.endswith('__')) or key not in self._dict:
      raise AttributeError("Did not find '%s'"%(key))
    else:
      val = self._dict[key]
      #self.__dict__[key] = val # cache
    return val
  
  def __getitem__(self,key):
    return self._dict[key]
  
  def __setattr__(self,key,val):
    if key in self.__dict__:
      self.__dict__[key] = val
    elif (key.startswith('__') and key.endswith('__')):
      raise AttributeError("Did not find '%s'"%(key))
    elif key.startswith('_'):
      self.__dict__[key] = val
    else:
      self._dict[key] = val
      #self.__dict__[key] = val # cache
    return val
  
  def __setitem__(self,key,val):
    self._dict[key] = val
    return val
  
  def __iter__(self):
    return iter(self._dict)
  
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
  
  def write(self,path=None):
    if path==None:
      path = self._path
    with open(path,'w') as outfile:
      json.dump(self._dict,outfile,indent=2)
    return path
  

