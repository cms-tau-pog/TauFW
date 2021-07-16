# Author: Izaak Neutelings (May 2020)
import os, glob
import getpass, platform
import importlib
from fnmatch import fnmatch
from TauFW.PicoProducer import basedir
from TauFW.common.tools.log import Logger
from TauFW.common.tools.file import ensurefile, ensureTFile
from TauFW.common.tools.utils import repkey, isglob
from ROOT import TFile
LOG  = Logger('Storage')
host = platform.node()


def getsedir():
  """Guess the storage element path for a given user and host."""
  user  = getpass.getuser()
  sedir = ""
  if 'lxplus' in host:
    sedir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    sedir = "/pnfs/psi.ch/cms/trivcat/store/user/%s/"%(user)
  elif "etp" in host:
    sedir = "/store/user/{}/".format(user)
  return sedir
  

def gettmpdirs():
  """Guess the temporary directory for a given user and host."""
  user  = getpass.getuser()
  tmphadddir = "/tmp/%s/"%(user) # temporary dir for creating intermediate hadd files
  tmpskimdir = ""                # temporary dir for creating skimmed file before copying to outdir
  if 'lxplus' in host:
    tmphadddir = "/eos/user/%s/%s/"%(user[0],user)
  elif "t3" in host and "psi.ch" in host:
    tmphadddir = basedir.rstrip('/')+'/' #output/$ERA/$CHANNEL/$SAMPLE/ #"/scratch/%s/"%(user)
  elif "etp" in host:
    tmphadddir = "/tmp/{}/".format(user)
  return tmpskimdir, tmphadddir
  

def getstorage(path,verb=0,ensure=False):
  """Guess the storage system based on the path."""
  if path.startswith('/eos/'):
    from TauFW.PicoProducer.storage.EOS import EOS
    storage = EOS(path,ensure=ensure,verb=verb)
  #elif path.startswith('/castor/'):
  #  storage = Castor(path,verb=verb)
  elif path.startswith('/pnfs/psi.ch/'):
    from TauFW.PicoProducer.storage.T3_PSI import T3_PSI
    storage = T3_PSI(path,ensure=ensure,verb=verb)
  elif path.startswith('/pnfs/desy.de/'):
    from TauFW.PicoProducer.storage.T2_DESY import T2_DESY
    storage = T2_DESY(path,ensure=ensure,verb=verb)
  elif path.startswith("/store/user") and ("etp" in host and "ekp" in host):
    from TauFW.PicoProducer.storage.GridKA_NRG import GridKA_NRG
    storage = GridKA_NRG(path,ensure=ensure,verb=verb)
  elif path.startswith('/pnfs/lcg.cscs.ch/'):
    from TauFW.PicoProducer.storage.T2_PSI import T2_PSI
    storage = T2_PSI(path,ensure=ensure,verb=verb)
  #elif path.startswith('/pnfs/iihe/'):
  #  return T2_IIHE(path,verb=verb)
  else:
    from TauFW.PicoProducer.storage.StorageSystem import Local
    storage = Local(path,ensure=ensure,verb=verb)
    if not os.path.exists(path):
      LOG.warning("Could not find storage directory %r. Make sure it exists and is mounted. "%(path)+\
                  "If it is a special system, you need to subclass StorageSystem, see "
                  "https://github.com/cms-tau-pog/TauFW/tree/master/PicoProducer#Storage-system")
  if verb>=2:
    print ">>> getstorage(%r), %r"%(path,storage)
  return storage
  

def getsamples(era,channel="",tag="",dtype=[],filter=[],veto=[],dasfilter=[],dasveto=[],moddict={},split=False,verb=0):
  """Help function to get samples from a sample list and filter if needed."""
  import TauFW.PicoProducer.tools.config as GLOB
  CONFIG   = GLOB.getconfig(verb=verb)
  filters  = filter  if not filter  or isinstance(filter,list)  else [filter]
  vetoes   = veto    if not veto    or isinstance(veto,list)    else [veto]
  dasveto  = dasveto if not dasveto or isinstance(dasveto,list) else [dasveto]
  dtypes   = dtype   if not dtype   or isinstance(dtype,list)   else [dtype]
  sampfile = ensurefile("samples",repkey(CONFIG.eras[era],ERA=era,CHANNEL=channel,TAG=tag))
  samppath = sampfile.replace('.py','').replace('/','.')
  LOG.verb("getsamples: sampfile=%r"%(sampfile),verb,1)
  LOG.verb("getsamples: samppath=%r"%(samppath),verb,3)
  if samppath not in moddict:
    moddict[samppath] = importlib.import_module(samppath) # cache; save time by loading once
  if not hasattr(moddict[samppath],'samples'):
    LOG.throw(IOError,"Module '%s' must have a list of Sample objects called 'samples'!"%(samppath))
  samplelist = moddict[samppath].samples
  samples    = [ ]
  sampledict = { } # ensure for unique names
  LOG.verb("getsamples: samplelist=%r"%(samplelist),verb,3)
  for sample in samplelist:
    if filters and not sample.match(filters,verb=verb): continue
    if vetoes and sample.match(vetoes,verb=verb): continue
    if dtypes and sample.dtype not in dtypes: continue
    if channel and sample.channels and not any(fnmatch(channel,c) for c in sample.channels): continue
    if sample.name in sampledict:
      LOG.throw(IOError,"Sample short names should be unique. Found two samples '%s'!\n\t%s\n\t%s"%(
                        sample.name,','.join(sampledict[sample.name].paths),','.join(sample.paths)))
    if dasfilter or dasveto:
      sample = sample.filterpath(filter=dasfilter,veto=dasveto,copy=True,verb=verb)
      if len(sample.paths)==0: continue
    if (split or 'skim' in channel) and sample.dosplit: # split samples with multiple DAS dataset paths, and submit as separate jobs
      for subsample in sample.split():
        samples.append(subsample) # keep correspondence sample to one sample in DAS
    else:
      samples.append(sample)
    sampledict[sample.name] = sample
  return samples
  

def getnevents(fname,treename='Events'):
  file = ensureTFile(fname)
  tree = file.Get(treename)
  if not tree:
    LOG.warning("getnevents: No %r tree in events in %r!"%(treename,fname))
    return 0
  nevts = tree.GetEntries()
  file.Close()
  return nevts
  

def isvalid(fname,hname='cutflow',bin=1):
  """Check if a given file is valid, or corrupt."""
  nevts = -1
  file  = TFile.Open(fname,'READ')
  if file and not file.IsZombie():
    if file.GetListOfKeys().Contains('Events'): # NANOAOD
      nevts = file.Get('Events').GetEntries()
      if nevts<=0:
        LOG.warning("'Events' tree of file %r has nevts=%s<=0..."%(fname,nevts))
    elif file.GetListOfKeys().Contains('tree') and file.GetListOfKeys().Contains(hname): # pico
      nevts = file.Get(hname).GetBinContent(bin)
      if nevts<=0:
        LOG.warning("Cutflow of file %r has nevts=%s<=0..."%(fname,nevts))
  return nevts
  

def itervalid(fnames,checkevts=True,nchunks=None,ncores=4,verb=0,**kwargs):
  """Iterate over file names and get number of events processed & check for corruption."""
  if not checkevts: # just skip validation step and return 0
    for fname in fnames:
      yield 0, fname
  elif ncores>=2 and len(fnames)>5: # run validation in parallel
    from TauFW.Plotter.plot.MultiThread import MultiProcessor
    from TauFW.common.tools.math import partition
    processor = MultiProcessor(max=ncores)
    def loopvalid(fnames_,**kwargs):
      """Help function for parallel running on subsets."""
      return [(isvalid(f,**kwargs),f) for f in fnames_]
    if not nchunks:
      nchunks = 10 if len(fnames)<100 else 20 if len(fnames)<500 else 50 if len(fnames)<1000 else 100
      nchunks = max(nchunks,2*ncores)
    if nchunks>=len(fnames):
      nchunks = len(fnames)-1
    if verb>=2:
      print ">>> itervalid: partitioning %d files into %d chunks for ncores=%d"%(len(fnames),nchunks,ncores)
    for i, subset in enumerate(partition(fnames,nchunks)): # process in ncores chunks
      if not subset: break
      name = "itervalid_%d"%(i)
      processor.start(loopvalid,subset,kwargs,name=name)
    for process in processor:
      if verb>=2:
        print ">>> joining process %r..."%(process.name)
      nevtfiles = process.join()
      for nevts, fname in nevtfiles:
        yield nevts, fname
  else:  # run validation in series
    for fname in fnames:
      if verb>=2:
        print ">>>   Validating job output '%s'..."%(fname)
      nevts = isvalid(fname)
      yield nevts, fname
  

def iterevts(fnames,tree,filenevts,refresh=False,nchunks=None,ncores=0,verb=0):
  """Help function for Sample._getnevents to iterate over file names and get number of events processed."""
  if ncores>=2 and len(fnames)>5: # run events check in parallel
    from TauFW.Plotter.plot.MultiThread import MultiProcessor
    from TauFW.common.tools.math import partition
    def loopevts(fnames_):
      """Help function for parallel running on subsets."""
      return [(getnevents(f,tree),f) for f in fnames_]
    processor = MultiProcessor(max=ncores)
    if not nchunks:
      nchunks = 10 if len(fnames)<100 else 20 if len(fnames)<500 else 50 if len(fnames)<1000 else 100
      nchunks = max(nchunks,2*ncores)
    if nchunks>=len(fnames):
      nchunks = len(fnames)-1
    if verb>=2:
      print ">>> iterevts: partitioning %d files into %d chunks for ncores=%d"%(len(fnames),nchunks,ncores)
    for i, subset in enumerate(partition(fnames,nchunks)): # process in ncores chunks
      for fname in subset[:]: # check cache
        if not refresh and fname in filenevts:
          nevts = filenevts[fname]
          subset.remove(fname) # don't run again
          yield nevts, fname
      if not subset:
        break
      name = "iterevts_%d"%(i)
      processor.start(loopevts,subset,name=name)
    for process in processor: # collect output from parallel processes
      if verb>=2:
        print ">>> iterevts: joining process %r..."%(process.name)
      nevtfiles = process.join()
      for nevts, fname in nevtfiles:
        yield nevts, fname
  else: # run events check in series
    for fname in fnames:
      if refresh or fname not in filenevts:
        nevts = getnevents(fname,tree)
      else: # get from cache or efficiency
        nevts = filenevts[fname]
      yield nevts, fname
  

def print_no_samples(dtype=[],filter=[],veto=[],jobdir="",jobcfgs=""):
  """Help function to print that no samples were found."""
  if jobdir and not glob.glob(jobdir): #os.path.exists(jobdir):
    print ">>> Job output directory %s does not exist!"%(jobdir)
  elif jobcfgs and not glob.glob(jobcfgs):
    print ">>> Did not find any job config files %s!"%(jobcfgs)
  else:
    string  = ">>> Did not find any samples"
    if filter or veto or (dtype and len(dtype)<3):
      strings = [ ]
      if filter:
        strings.append("filters '%s'"%("', '".join(filter)))
      if veto:
        strings.append("vetoes '%s'"%("', '".join(veto)))
      if dtype and len(dtype)<3:
        strings.append("data types '%s'"%("', '".join(dtype)))
      string += " with "+', '.join(strings)
    print string
  print
  
