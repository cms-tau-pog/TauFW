# Author: Izaak Neutelings (May 2020)
# Redirector URLs:
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
from TauFW.common.tools.utils import execute, CalledProcessError, repkey, ensurelist, isglob
from TauFW.common.tools.file import ensurefile, ensureTFile
from TauFW.PicoProducer.tools.config import _user
from TauFW.PicoProducer.storage.utils import LOG, getstorage
dasurls = ["root://cms-xrd-global.cern.ch/","root://xrootd-cms.infn.it/", "root://cmsxrootd.fnal.gov/"]


def dasgoclient(query,**kwargs):
  """Help function to call dasgoclient."""
  try:
    verbosity = kwargs.get('verb',  0  )
    limit     = kwargs.get('limit', 0  )
    option    = kwargs.get('opts',  "" )
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
  

class Sample(object):
  
  def __init__(self,group,name,*paths,**kwargs):
    """Container class for CMSSW samples, e.g.:
       - group: DY (used to group similar samples in final output)
       - name:  DYJetsToLL_M-50 (used as shorthand and jobname)
       - path:  /DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6_Nano25Oct2019_102X_mcRun2/NANOAODSIM
       - dtype: 'mc', 'data', 'embed'
    """
    
    # PATH
    LOG.insist(len(paths)>=1,"Need at least one path to create a sample...")
    if len(paths)==1 and isinstance(paths[0],list):
      paths = paths[0]
    for path in paths:
      LOG.insist(path.count('/')>=3 and path.startswith('/'),"DAS path %r has wrong format. Need /SAMPLE/CAMPAIGN/FORMAT."%(path))
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
      dtype = 'mc' # TODO: remove
    LOG.insist(dtype in dtypes,"Given data type '%s' is not recongized! Please choose from %s..."%(dtype,', '.join(dtypes)))
    
    # ATTRIBUTES
    self.group        = group
    self.name         = name
    self.paths        = paths # DAS dataset path
    self.dtype        = dtype
    self.channels     = kwargs.get('channel',      None )
    self.channels     = kwargs.get('channels',     self.channels )
    self.storage      = None
    self.storepath    = kwargs.get('store',        None ) # if stored elsewhere than DAS
    self.url          = kwargs.get('url',          None )
    self.dasurl       = kwargs.get('dasurl',       None ) or "root://cms-xrd-global.cern.ch/"
    self.blacklist    = kwargs.get('blacklist',    [ ]  ) # black list file
    self.instance     = kwargs.get('instance', 'prod/phys03' if path.endswith('USER') else 'prod/global') # if None, does not exist in DAS
    self.nfilesperjob = kwargs.get('nfilesperjob', -1   ) # number of nanoAOD files per job
    self.extraopts    = kwargs.get('opts',         [ ]  ) # extra options for analysis module, e.g. ['doZpt=1','tes=1.1']
    self.subtry       = kwargs.get('subtry',       0    ) # to help keep track of resubmission
    self.jobcfg       = kwargs.get('jobcfg',       { }  ) # to help keep track of resubmission
    self.nevents      = kwargs.get('nevts',        0    ) # number of nanoAOD events that can be processed
    self.nevents      = kwargs.get('nevents',      self.nevents )
    self.files        = kwargs.get('files',        [ ]  ) # list of ROOT files, OR text file with list of files
    self.postfix      = kwargs.get('postfix',      None ) or "" # post-fix (before '.root') for stored ROOT files
    self.era          = kwargs.get('era',          ""   ) # for expansion of $ERA variable
    self.dosplit      = kwargs.get('split', len(self.paths)>=2 ) # allow splitting (if multiple DAS datasets)
    self.verbosity    = kwargs.get('verbosity',     0   ) # verbosity level for debugging
    self.refreshable  = not self.files                   # allow refresh on file list in getfiles()
    
    # ENSURE LIST
    if self.channels!=None and not isinstance(self.channels,list):
      self.channels = [self.channels]
    if isinstance(self.extraopts,str):
      if ',' in self.extraopts:
        self.extraopts = self.extraopts.split(',')
      self.extraopts = [self.extraopts]
    
    # STORAGE & URL DEFAULTS
    if self.storepath:
      self.storepath = repkey(self.storepath,USER=_user,ERA=self.era,GROUP=self.group,SAMPLE=self.name)
      self.storage = getstorage(repkey(self.storepath,PATH=self.paths[0],DAS=self.paths[0]),ensure=False)
    if not self.dasurl:
      self.dasurl = self.url if (self.url in dasurls) else dasurls[0]
    if not self.url:
      if self.storepath:
        if self.storage.__class__.__name__=='Local':
          self.url = "" #root://cms-xrd-global.cern.ch/
        else:
          self.url = self.storage.fileurl
      else:
        self.url = self.dasurl
    
    # GET FILE LIST FROM TEXT FILE
    if isinstance(self.files,str):
      filename = repkey(self.files,ERA=self.era,GROUP=self.group,SAMPLE=self.name)
      if self.verbosity>=1:
        print ">>> Loading sample files from '%r'"%(filename)
      if self.verbosity>=2:
        print ">>> %-14s = %s"%('filelist',self.files)
        print ">>> %-14s = %s"%('filename',filename)
      filelist = [ ]
      with open(filename,'r') as file:
        for line in file:
          line = line.strip().split()
          if not line: continue
          infile = line[0].strip()
          if infile[0]=='#': continue
          if infile.endswith('.root'):
            filelist.append(infile)
      self.files = filelist
      self.files.sort()
  
  def __str__(self):
    return self.name
  
  def __repr__(self):
    return '<%s("%s") at %s>'%(self.__class__.__name__,self.name,hex(id(self)))
  
  @staticmethod
  def loadjson(cfgname):
    """Initialize sample from job config JSON file."""
    with open(cfgname,'r') as file:
      jobcfg = json.load(file)
    for key, value in jobcfg.items():
      if isinstance(value,unicode):
        jobcfg[key] = str(value)
    for key in ['group','name','paths','try','channel','chunkdict','dtype','extraopts']:
      LOG.insist(key in jobcfg,"Did not find key '%s' in job configuration %s"%(key,cfgname))
    jobcfg['config']    = str(cfgname)
    jobcfg['chunkdict'] = { int(k): v for k, v in jobcfg['chunkdict'].iteritems() }
    nfilesperjob        = int(jobcfg['nfilesperjob'])
    dtype    = jobcfg['dtype']
    channels = [jobcfg['channel']]
    opts     = [str(s) for s in jobcfg['extraopts']]
    subtry   = int(jobcfg['try'])
    nevents  = int(jobcfg['nevents'])
    sample   = Sample(jobcfg['group'],jobcfg['name'],jobcfg['paths'],dtype=dtype,channels=channels,
                      subtry=subtry,jobcfg=jobcfg,nfilesperjob=nfilesperjob,nevents=nevents,opts=opts)
    return sample
  
  def split(self,tag="ext"):
    """Split if multiple DAS dataset paths."""
    samples = [ ]
    if self.dosplit:
      for i, path in enumerate(self.paths):
        sample = deepcopy(self)
        if i>0:
          sample.name += "_%s%d"%(tag,i) # rename to distinguish jobs
        sample.paths = [path]
        sample.dosplit = False
        samples.append(sample)
    else:
      samples.append(self)
    return samples
  
  def match(self,patterns,verb=0):
    """Match sample name to some (glob) pattern."""
    patterns = ensurelist(patterns)
    sample   = self.name.strip('/')
    match_   = False
    for pattern in patterns:
      if isglob(pattern):
        if fnmatch(sample,pattern+'*'):
          match_ = True
          break
      else:
        if pattern in sample[:len(pattern)+1]:
          match_ = True
          break
    if verb>=2:
      if match_:
        print ">>> Sample.match: '%s' match to '%s'!"%(sample,pattern)
      else:
        print ">>> Sample.match: NO '%s' match to '%s'!"%(sample,pattern)
    return match_
  
  def getfiles(self,das=False,refresh=False,url=True,limit=-1,verb=0):
    """Get list of files from storage system (default), or DAS (if no storage system of das=True)."""
    files   = self.files
    url_    = self.dasurl if (das and self.storage) else self.url
    if self.refreshable and (not files or das or refresh):
      files = [ ]
      for daspath in self.paths:
        if (self.storage and not das) or (not self.instance): # get files from storage system
          postfix = self.postfix+'.root'
          sepath  = repkey(self.storepath,PATH=daspath,DAS=daspath).replace('//','/')
          outlist = self.storage.getfiles(sepath,url=url,verb=verb-1)
          if limit>0:
            outlist = outlist[:limit]
        else: # get files from DAS
          postfix = '.root'
          cmdout  = dasgoclient("file dataset=%s instance=%s"%(daspath,self.instance),limit=limit,verb=verb-1)
          outlist = cmdout.split(os.linesep)
        for line in outlist: # filter root files
          line = line.strip()
          if line.endswith(postfix) and not any(f.endswith(line) for f in self.blacklist):
            if url and url_ not in line and 'root://' not in line:
              line = url_+line
            files.append(line)
      files.sort() # for consistent list order
      if not das or not self.storage:
        self.files = files # save for efficiency
    elif url and any(url_ not in f for f in files): # add url if missing
      files = [(url_+f if url_ not in f else f) for f in files]
    elif not url and any(url_ in f for f in files): # remove url
      files = [f.replace(url_,"") for f in files]
    return files
  
  def getnevents(self,das=True,refresh=False,treename='Events',verb=0):
    """Get number of nanoAOD events from DAS (default), or from files on storage system (das=False)."""
    nevents = self.nevents
    if nevents<=0 or refresh:
      if self.storage and not das: # get number of events from storage system
        files = self.getfiles(url=True,refresh=refresh,verb=verb)
        for fname in files:
          file     = ensureTFile(fname)
          tree     = file.Get(treename)
          if not tree:
            LOG.warning("getnevents: No %r tree in events in %r!"%('Events',fname))
            continue
          nevts    = tree.GetEntries()
          file.Close()
          nevents += nevts
          LOG.verb("getnevents: Found %d events in %r."%(nevts,fname),verb,3)
      else: # get number of events from DAS
        for daspath in self.paths:
          cmdout = dasgoclient("summary dataset=%s instance=%s"%(daspath,self.instance),verb=verb-1)
          if "nevents" in cmdout:
            ndasevts = int(cmdout.split('"nevents":')[1].split(',')[0])
          else:
            ndasevts = 0
            LOG.warning("Could not get number of events from DAS for %r."%(self.name))
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
  

