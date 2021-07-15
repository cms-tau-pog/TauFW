# Author: Izaak Neutelings (May 2020)
# Redirector URLs:
#   root://cms-xrd-global.cern.ch/ # DAS, globally
#   root://xrootd-cms.infn.it/     # DAS, use in Eurasia
#   root://cmsxrootd.fnal.gov/     # DAS, use in the US
#   root://t3dcachedb.psi.ch:1094/ # PSI T3
#   root://storage01.lcg.cscs.ch/  # PSI T2
#   root://cmseos.fnal.gov/        # Fermi lab
import os, re, json
import gzip
import importlib
from copy import deepcopy
from fnmatch import fnmatch
from TauFW.common.tools.utils import repkey, ensurelist, isglob
from TauFW.common.tools.file import ensuredir, ensurefile, ensureTFile
from TauFW.common.tools.LoadingBar import LoadingBar
import TauFW.PicoProducer.tools.config as GLOB
#from TauFW.PicoProducer.tools.config import user
from TauFW.PicoProducer.storage.utils import LOG, getstorage, getnevents, iterevts
from TauFW.PicoProducer.storage.das import dasgoclient, getdasnevents, getdasfiles
dasurls = ["root://cms-xrd-global.cern.ch/","root://xrootd-cms.infn.it/", "root://cmsxrootd.fnal.gov/"]
fevtsexp = re.compile(r"(.+\.root)(?::(\d+))?$") # input file stored in lis in text file



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
    self.channels     = kwargs.get('channel',       None   )
    self.channels     = kwargs.get('channels', self.channels )
    self.storage      = None
    self.storepath    = kwargs.get('store',         None   ) # if stored elsewhere than DAS
    self.url          = kwargs.get('url',           None   ) # URL if stored elsewhere
    self.dasurl       = kwargs.get('dasurl',        None   ) or "root://cms-xrd-global.cern.ch/" # URL for DAS
    self.blacklist    = kwargs.get('blacklist',     [ ]    ) # black list for ROOT files
    self.instance     = kwargs.get('instance', 'prod/phys03' if path.endswith('USER') else 'prod/global') # if None, does not exist in DAS
    self.nfilesperjob = kwargs.get('nfilesperjob',  -1     ) # number of nanoAOD files per job
    self.maxevts      = kwargs.get('maxevtsperjob', -1     ) # maximum number of events processed per job
    self.maxevts      = kwargs.get('maxevts', self.maxevts ) # maximum number of events processed per job
    self.extraopts    = kwargs.get('opts',          [ ]    ) # extra options for analysis module, e.g. ['doZpt=1','tes=1.1']
    self.subtry       = kwargs.get('subtry',        0      ) # to help keep track of resubmission
    self.jobcfg       = kwargs.get('jobcfg',        { }    ) # to help keep track of resubmission
    self.nevents      = kwargs.get('nevts',         0      ) # number of nanoAOD events that can be processed
    self.nevents      = kwargs.get('nevents', self.nevents ) # cache of number of events
    self.filelist     = None # text file
    self.files        = kwargs.get('files',         [ ]    ) # list of ROOT files, OR text file with list of files
    if isinstance(self.files,str):
      self.filelist = self.files.replace("$SAMPLE",name) # text file
      self.files    = [ ] # list of ROOT files
    self.pathfiles    = { } # dictionary of DAS dataset path -> file list
    self.filenevts    = kwargs.get('filenevts',     { }    ) # cache of number of events for each file; might speed up event splitting, if sample is submitted multiple times
    self.postfix      = kwargs.get('postfix',       None   ) or "" # post-fix (before '.root') for stored ROOT files
    self.era          = kwargs.get('era',           ""     ) # for expansion of $ERA variable
    self.dosplit      = kwargs.get('split', len(self.paths)>=2 ) # allow splitting (if multiple DAS datasets)
    self.verbosity    = kwargs.get('verbosity', LOG.verbosity ) # verbosity level for debugging
    self.refreshable  = not self.files                       # allow refresh of file list in getfiles()
    
    # ENSURE LIST
    if self.channels!=None and not isinstance(self.channels,list):
      self.channels = [self.channels]
    if isinstance(self.extraopts,str):
      if ',' in self.extraopts:
        self.extraopts = self.extraopts.split(',')
      else:
        self.extraopts = [self.extraopts]
    
    # STORAGE & URL DEFAULTS
    if self.storepath:
      self.storepath = repkey(self.storepath,USER=GLOB.user,ERA=self.era,GROUP=self.group,SAMPLE=self.name)
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
    
    # VERBOSITY
    if self.verbosity>=3:
      print ">>> Sample.__init__: %r from group %r and type %r"%(self.name,self.group,self.dtype)
      print ">>>   %-11s = %s"%('paths',self.paths)
      print ">>>   %-11s = %r"%('storage',self.storage)
      print ">>>   %-11s = %r, %r"%('url, dasurl',self.url,self.dasurl)
      print ">>>   %-11s = %r"%('filelist',self.filelist)
      print ">>>   %-11s = %s"%('filenevts',self.filenevts)
      print ">>>   %-11s = %s"%('nevents',self.nevents)
      print ">>>   %-11s = %r"%('extraopts',self.extraopts)
  
  def __str__(self):
    return self.name
  
  def __repr__(self):
    return '<%s("%s") at %s>'%(self.__class__.__name__,self.name,hex(id(self)))
  
  @staticmethod
  def loadjson(cfgname):
    """Initialize sample from job config JSON file."""
    if cfgname.endswith(".json.gz"):
      with gzip.open(cfgname,'rt') as file:
        data = file.read().strip()
        jobcfg = json.loads(data)
    else:
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
    filenevts = jobcfg.get('filenevts',{ })
    dtype     = jobcfg['dtype']
    channels  = [jobcfg['channel']]
    opts      = [str(s) for s in jobcfg['extraopts']]
    subtry    = int(jobcfg['try'])
    nevents   = int(jobcfg['nevents'])
    sample    = Sample(jobcfg['group'],jobcfg['name'],jobcfg['paths'],dtype=dtype,channels=channels,
                       subtry=subtry,jobcfg=jobcfg,nfilesperjob=nfilesperjob,filenevts=filenevts,nevents=nevents,opts=opts)
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
  
  def filterpath(self,filter=[],veto=[],copy=False,verb=0):
    """Filter DAS paths by matching to (glob) pattern. Update this sample, or create copy"""
    paths = [ ]
    sample = self
    for path in self.paths:
      keep = not filter or any(fnmatch(path,'*'+f+'*') for f in filter)
      if veto:
        keep = not any(fnmatch(path,'*'+f+'*') for f in veto)
      if keep:
        paths.append(path)
    if verb>=1:
      print ">>> Sample.filterpath: filters=%s, vetoes=%s, %s -> %s"%(filter,veto,self.paths,paths)
    if len(paths)!=len(self.paths):
      if copy:
        sample = deepcopy(self)
      sample.paths = paths
      for path in sample.pathfiles.keys():
        if path not in paths:
          sample.pathfiles.pop(path)
    return sample
  
  def getfiles(self,das=False,refresh=False,url=True,limit=-1,verb=0):
    """Get list of files from storage system (default), or DAS (if no storage system of das=True)."""
    LOG.verb("getfiles: das=%r, refresh=%r, url=%r, limit=%r, filelist=%r, len(files)=%d, len(filenevts)=%d"%(
      das,refresh,url,limit,self.filelist,len(self.files),len(self.filenevts)),verb,1)
    if self.filelist and not self.files: # get file list from text file for first time
      self.loadfiles(self.filelist)
    files = self.files # cache for efficiency
    url_  = self.dasurl if (das and self.storage) else self.url
    if self.refreshable and (not files or das or refresh): # (re)derive file list
      if not files or das:
        LOG.verb("getfiles: Retrieving files...",verb,2)
      else:
        LOG.verb("getfiles: Refreshing file list...",verb,2)
      files = [ ]
      for daspath in self.paths: # loop over DAS dataset paths
        self.pathfiles[daspath] = [ ]
        if (self.storage and not das) or (not self.instance): # get files from storage system
          postfix = self.postfix+'.root'
          sepath  = repkey(self.storepath,PATH=daspath,DAS=daspath).replace('//','/')
          outlist = self.storage.getfiles(sepath,url=url,verb=verb-1)
          if limit>0:
            outlist = outlist[:limit]
        else: # get files from DAS
          postfix = '.root'
          outlist = getdasfiles(daspath,instance=self.instance,limit=limit,verb=verb-1)
        for line in outlist: # filter root files
          line = line.strip()
          if line.endswith(postfix) and not any(f.endswith(line) for f in self.blacklist):
            if url and url_ not in line and 'root://' not in line:
              line = url_+line
            files.append(line)
            self.pathfiles[daspath].append(line)
        self.pathfiles[daspath].sort()
        if not self.pathfiles[daspath]:
          LOG.warning("getfiles: Did not find any files for %s"%(daspath))
      files.sort() # for consistent list order
      if not das or not self.storage:
        self.files = files # store cache for efficiency
    elif url and any(url_ not in f for f in files): # add url if missing
      files = [(url_+f if url_ not in f else f) for f in files]
    elif not url and any(url_ in f for f in files): # remove url
      files = [f.replace(url_,"") for f in files]
    return files[:] # pass copy to protect private self.files
  
  def _getnevents(self,das=True,refresh=False,tree='Events',limit=-1,checkfiles=False,ncores=0,verb=0):
    """Get number of nanoAOD events from DAS (default), or from files on storage system (das=False)."""
    LOG.verb("_getnevents: das=%r, refresh=%r, tree=%r, limit=%r, checkfiles=%r, filelist=%r, len(files)=%d, len(filenevts)=%d"%(
      das,refresh,tree,limit,checkfiles,self.filelist,len(self.files),len(self.filenevts)),verb,1)
    if self.filelist and not self.files: # get file list from text file for first time
      self.loadfiles(self.filelist)
    nevents   = self.nevents
    filenevts = self.filenevts
    bar       = None
    if nevents<=0 or refresh:
      if checkfiles or (self.storage and not das): # get number of events per file from storage system
        LOG.verb("_getnevents: Get events per file (storage=%r, das=%r)..."%(self.storage,das),verb,2)
        files = self.getfiles(url=True,das=das,refresh=refresh,limit=limit,verb=verb)
        if verb<=0 and len(files)>=5:
          bar = LoadingBar(len(files),width=20,pre=">>> Getting number of events: ",counter=True,remove=True)
        for nevts, fname in iterevts(files,tree,filenevts,refresh,ncores=ncores,verb=verb):
          filenevts[fname] = nevts # cache
          nevents += nevts
          LOG.verb("_getnevents: Found %d events in %r."%(nevts,fname),verb,3)
          if bar:
             if self.nevents>0:
               bar.count("files, %d/%d events (%d%%)"%(nevents,self.nevents,100.0*nevents/self.nevents))
             else:
               bar.count("files, %d events"%(nevents))
      else: # get total number of events from DAS
        LOG.verb("_getnevents: Get total number of events per path (storage=%r, das=%r)..."%(self.storage,das),verb,2)
        for daspath in self.paths:
          nevts = getdasnevents(daspath,instance=self.instance,verb=verb-1)
          LOG.verb("_getnevents: %10d events for %s..."%(nevts,daspath),verb,2)
          nevents += nevts
      if limit<=0:
        self.nevents = nevents
    else:
      LOG.verb("_getnevents: Reusing old number of events (nevents=%r, refresh=%r)..."%(nevents,refresh),verb,2)
    return nevents, filenevts
  
  def getfilenevts(self,*args,**kwargs):
    """Get number of nanoAOD events per file."""
    return self._getnevents(*args,**kwargs)[1]
  
  def getnevents(self,*args,**kwargs):
    """Get number of nanoAOD events."""
    return self._getnevents(*args,**kwargs)[0]
  
  def writefiles(self,listname,**kwargs):
    """Write filenames to text file for fast look up in future.
    If there is more than one DAS dataset path, write lists separately for each path."""
    kwargs    = kwargs.copy() # do not edit given dictionary
    writeevts = kwargs.pop('nevts',False) # also write nevents to file
    listname  = repkey(listname,ERA=self.era,GROUP=self.group,SAMPLE=self.name)
    ensuredir(os.path.dirname(listname))
    filenevts = self.getfilenevts(checkfiles=True,**kwargs) if writeevts else None
    treename  = kwargs.pop('tree','Events') # do not pass to Sample.getfiles
    kwargs.pop('ncores') # do not pass to Sample.getfiles
    kwargs['refresh'] = False # already got file list in Sample.filenevts
    files     = self.getfiles(**kwargs) # get right URL
    if not files:
      LOG.warning("writefiles: Did not find any files!")
    def _writefile(ofile,fname,prefix=""):
      """Help function to write individual files."""
      if writeevts: # add nevents at end of infile string
        nevts = filenevts.get(fname,-1) # retrieve from cache
        if nevts<0:
          LOG.warning("Did not find nevents of %s. Trying again..."%(fname))
          nevts = getnevents(fname,treename) # get nevents from file
        fname = "%s:%d"%(fname,nevts) # write $FILENAM(:NEVTS)
      ofile.write(prefix+fname+'\n')
    paths = self.paths if '$PATH' in listname else [self.paths[0]]
    for path in paths:
      listname_ = repkey(listname,PATH=path.strip('/').replace('/','__'))
      with open(listname_,'w+') as lfile:
        if '$PATH' in listname: # write only the file list of this path to this text file
          print ">>> Write %s files to list %r..."%(len(self.pathfiles[path]),listname_)
          for infile in self.pathfiles[path]:
            _writefile(lfile,infile)
        elif len(self.paths)<=1: # write file list for the only path
          if self.nevents>0:
            print ">>> Write %s files to list %r..."%(len(files),listname_)
          else:
            print ">>> Write %s files (%d events) to list %r..."%(len(files),self.nevents,listname_)
          for infile in files:
            _writefile(lfile,infile)
        else: # divide up list per DAS dataset path
          if self.nevents>0:
            print ">>> Write %s files to list %r..."%(len(files),listname_)
          else:
            print ">>> Write %s files (%d events) to list %r..."%(len(files),self.nevents,listname_)
          for i, path in enumerate(self.paths):
            print ">>>   %3s files for %s..."%(len(self.pathfiles[path]),path)
            lfile.write("DASPATH=%s\n"%(path)) # write special line to text file, which loadfiles() can parse
            for infile in self.pathfiles[path]: # loop over this list (general list is sorted)
              LOG.insist(infile in files,"Did not find file %s in general list! %s"%(infile,files))
              _writefile(lfile,infile,prefix="  ")
            if i+1<len(self.paths): # add extra white line between blocks
              lfile.write("\n")
  
  def loadfiles(self,listname_,**kwargs):
    verbosity = LOG.getverbosity(self,kwargs)
    """Load filenames from text file for fast look up in future."""
    listname  = repkey(listname_,ERA=self.era,GROUP=self.group,SAMPLE=self.name)
    LOG.verb("loadfiles: listname=%r -> %r, len(files)=%d, len(filenevts)=%d"%(
      listname_,listname,len(self.files),len(self.filenevts)),verbosity,1)
    filenevts = self.filenevts
    nevents   = 0
    #listname = ensurefile(listname,fatal=False)
    filelist = [ ]
    paths = self.paths if '$PATH' in listname else [self.paths[0]]
    for path in paths:
      listname_ = repkey(listname,PATH=path.strip('/').replace('/','__'))
      if self.verbosity>=1:
        print ">>> Loading sample files from %r..."%(listname_)
      self.pathfiles[path] = [ ]
      if os.path.isfile(listname_):
        skip = False
        subpaths = [ ] # for sanity check
        with open(listname_,'r') as file:
          for line in file:
            line = line.strip().split() # split at space to allow comments at end
            if not line: continue
            line = line[0].strip() # remove spaces, consider only first part of the line
            if line[0]=='#': continue # do not consider comments
            #if line.endswith('.root'):
            if line.startswith("DASPATH="): # to keep track of multiple DAS data set paths
              path = line.split('=')[-1] # DAS data set path
              LOG.insist(path.count('/')>=3 and path.startswith('/'),
                "DAS path %r in %s has wrong format. Need /SAMPLE/CAMPAIGN/FORMAT..."%(path,listname_))
              if path in self.paths: # store file list for this path
                self.pathfiles[path] = [ ]
                subpaths.append(path)
                skip = False
              else: # do not store file list for this path
                skip = True
            else:
              if skip: continue # only load files for this sample's DAS dataset paths
              match = fevtsexp.match(line) # match $FILENAM(:NEVTS)
              if not match: continue
              infile = match.group(1)
              if match.group(2): # found nevents in filename
                nevts  = int(match.group(2))
                filenevts[infile] = nevts # store/cache in dictionary
                nevents += nevts
              filelist.append(infile)
              self.pathfiles[path].append(infile)
              if self.verbosity>=3:
                print ">>> %7d events for %s"%(nevts,infile)
        if not filelist:
          LOG.warning("loadfiles: Did not find any files in %s!"%(listname_))
          self.refreshable = True
        else: # sanity check for empty list
          for subpath in subpaths:
            if not self.pathfiles[subpath]:
              LOG.warning("loadfiles: Did not find any files for path %s in %s!"%(subpath,listname_))
      else:
        LOG.warning("loadfiles: file list %s does not exist!"%(listname_))
        self.refreshable = True
    for path in self.paths:
      if path not in self.pathfiles: # nonexistent list
        LOG.warning("loadfiles: Did not find any files for path %s in %s!"%(path,listname))
    if self.nevents<=0:
      self.nevents = nevents
    elif self.nevents!=nevents:
      LOG.warning("loadfiles: stored nevents=%d does not match the sum total of file events, %d!"%(self.nevents,nevents))
      self.nevents == nevents
    self.files = filelist
    self.files.sort()
    return self.files
  

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
  

