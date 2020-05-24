#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Directors:
#   root://cms-xrd-global.cern.ch/ # DAS, globally
#   root://xrootd-cms.infn.it/     # DAS, use in Eurasia
#   root://cmsxrootd.fnal.gov/     # DAS, use in the US
#   root://t3dcachedb.psi.ch:1094/ # PSI T3
#   root://storage01.lcg.cscs.ch/  # PSI T2
#   root://cmseos.fnal.gov/        # Fermi lab
import os, re, json
import importlib
from copy import deepcopy
from fnmatch import fnmatch
from TauFW.PicoProducer.tools.utils import execute, repkey
from TauFW.PicoProducer.tools.file import ensurefile
from TauFW.PicoProducer.storage.StorageSystem import getstorage


class Sample(object):
  
  def __init__(self,group,name,*paths,**kwargs):
    """Container class for CMSSW samples, e.g.:
       - group: DY (used to group similar samples in final output)
       - name:  DYJetsToLL_M-50 (used as shorthand and jobname)
       - path:  /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6_Nano25Oct2019_102X_mcRun2/NANOAODSIM
       - dtype: mc
    """
    
    # PATH
    assert len(paths)>=1, "Need at least one path to create a sample..."
    if len(paths)==1 and isinstance(paths[0],list):
      paths = paths[0]
    for path in paths:
      assert path.count('/')>=3 and path.startswith('/'), "Path %s has wrong format. Need /SAMPLE/CAMPAIGN/FORMAT."
      #sample = '/'.join(line.split('/')[-3:])
    
    # DATA TYPE
    dtype  = kwargs.get('dtype', None)
    dtypes = ['mc','data','embed']
    if dtype==None: # automatic recognition
      path = paths[0]
      if 'Embed' in path:
        dtype = 'embed'
      elif path.endswith('SIM') or any(g in path for g in ['pythia','madgraph']):
        dtype = 'mc'
      elif re.search(r"/Run20\d\d",path):
        dtype = 'data'
    assert dtype in dtypes, "Given data type '%s' is not recongized! Please choose from %s..."%(dtype,', '.join(dtypes))
    
    # ATTRIBUTES
    self.group        = group
    self.name         = name
    self.paths        = paths # DAS path
    self.dtype        = dtype
    self.channels     = kwargs.get('channels',     None)
    self.director     = kwargs.get('director',     "root://cms-xrd-global.cern.ch/")
    self.storage      = kwargs.get('store',        None) # if stored elsewhere than DAS
    self.blacklist    = kwargs.get('blacklist',    [ ] ) # black list file
    self.instance     = kwargs.get('instance',     'prod/phys03' if path.endswith('USER') else 'prod/global')
    self.nfilesperjob = kwargs.get('nfilesperjob', -1  )
    self.subtry       = kwargs.get('subtry',        0  ) # to help keep track of resubmission
    self.jobcfg       = kwargs.get('jobcfg',       { } ) # to help keep track of resubmission
    self.nevents      = kwargs.get('nevents',        0 )
    self.files        = kwargs.get('files',        [ ] )
  
  def __str__(self):
    return self.name
  
  def __repr__(self):
    return '<%s("%s") at %s>'%(self.__class__.__name__,self.name,hex(id(self)))
  
  @staticmethod
  def loadJSON(cfgname):
    """Initialize sample from job config JSON file."""
    with open(cfgname,'r') as file:
      jobcfg = json.load(file)
    for key in ['group','name','paths','try','channel','chunkdict']:
      assert key in jobcfg, "Did not find key '%s' in %s"%(key,cfgname)
    jobcfg['config']    = cfgname
    jobcfg['chunkdict'] = { int(k): v for k, v in jobcfg['chunkdict'].iteritems() }
    nfilesperjob        = int(jobcfg['nfilesperjob'])
    channels = [jobcfg['channel']]
    subtry   = int(jobcfg['try'])
    nevents  = int(jobcfg['nevents'])
    sample   = Sample(jobcfg['group'],jobcfg['name'],jobcfg['paths'],channels=channels,
                      subtry=subtry,jobcfg=jobcfg,nfilesperjob=nfilesperjob,nevents=nevents)
    return sample
  
  def split(self):
    """Split if multiple das paths."""
    samples = [ ]
    for i, path in enumerate(self.paths):
      sample = deepcopy(self)
      if i>1:
        sample.name += "_ext%d"%i
      sample.paths = [path]
      samples.append(sample)
    return samples
  
  def match(self,patterns,verb=0):
    """Match sample name to some pattern."""
    sample = self.name.strip('/')
    if not isinstance(patterns,list):
      patterns = [patterns]
    match_ = False
    for pattern in patterns:
      if '*' in pattern or '?' in pattern or ('[' in pattern and ']' in pattern):
        if fnmatch(sample,pattern+'*'):
          match_ = True
          break
      else:
        if pattern in sample[:len(pattern)+1]:
          match_ = True
          break
    if verb>=2:
      if match_: print ">>> Sample.match: '%s' match to '%s'!"%(sample,pattern)
      else:      print ">>> Sample.match: NO '%s' match to '%s'!"%(sample,pattern)
    return match_
  
  def getfiles(self,refresh=False,verb=0):
    """Get list of files from DAS."""
    files = self.files
    if not files or refresh:
      files = [ ]
      for path in self.paths:
        if self.storage:
          storage = getstorage(repkey(self.storage,GROUP=self.group,SAMPLE=self.name,PATH=path),verb=verb)
          print storage
          outlist = storage.getfiles(verb=verb)
        else:
          dascmd  = 'dasgoclient --limit=0 --query="file dataset=%s instance=%s"'%(path,self.instance)
          cmdout  = execute(dascmd,verb=verb)
          outlist = cmdout.split(os.linesep)
        for line in outlist:
          line = line.strip()
          if line.endswith('.root') and not any(f.endswith(line) for f in self.blacklist):
            files.append(self.director+line)
      files.sort() # for consistent list order
      self.files = files
    return files
  
  def getnevents(self,refresh=False,verb=0):
    """Get number of files from DAS."""
    nevents = self.nevents
    if nevents<=0 or refresh:
      for path in self.paths:
        dascmd   = 'dasgoclient --limit=0 --query="summary dataset=%s instance=%s"'%(path,self.instance)
        cmdout   = execute(dascmd,verb=verb)
        ndasevts = int(cmdout.split('"nevents":')[1].split(',')[0])
        nevents += ndasevts
      self.nevents = nevents
    return nevents
  

class Data(Sample):
  def __init__(self,*args,**kwargs):
    kwargs['dtype'] = 'data'
    super(Data,self).__init__(*args,**kwargs)
  

class MC(Sample):
  def __init__(self,*args,**kwargs):
    kwargs['dtype'] = 'mc'
    super(MC,self).__init__(*args,**kwargs)
  

class Embdedded(Sample):
  def __init__(self,*args,**kwargs):
    kwargs['dtype'] = 'embed'
    super(Embdedded,self).__init__(*args,**kwargs)
  

