# Author: Izaak Neutelings (May 2020)
import os
import getpass, platform
import importlib
from fnmatch import fnmatch
from TauFW.PicoProducer import basedir
from TauFW.common.tools.log import Logger
from TauFW.common.tools.file import ensurefile
from TauFW.common.tools.utils import repkey, isglob
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
  elif path.startswith("/store/user") and "etp" in host:
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
  

def getsamples(era,channel="",tag="",dtype=[],filter=[],veto=[],moddict={},verb=0):
  """Help function to get samples from a sample list and filter if needed."""
  import TauFW.PicoProducer.tools.config as GLOB
  CONFIG   = GLOB.getconfig(verb=verb)
  filters  = filter if not filter or isinstance(filter,list) else [filter]
  vetoes   = veto   if not veto   or isinstance(veto,list)   else [veto]
  dtypes   = dtype  if not dtype  or isinstance(dtype,list)  else [dtype]
  sampfile = ensurefile("samples",repkey(CONFIG.eras[era],ERA=era,CHANNEL=channel,TAG=tag))
  samppath = sampfile.replace('.py','').replace('/','.')
  if samppath not in moddict:
    moddict[samppath] = importlib.import_module(samppath) # save time by loading once
  if not hasattr(moddict[samppath],'samples'):
    LOG.throw(IOError,"Module '%s' must have a list of Sample objects called 'samples'!"%(samppath))
  samplelist = moddict[samppath].samples
  samples    = [ ]
  sampledict = { } # ensure for unique names
  LOG.verb("getsamples: samplelist=%r"%(samplelist),verb,3)
  for sample in samplelist:
    if filters and not sample.match(filters,verb): continue
    if vetoes and sample.match(vetoes,verb): continue
    if dtypes and sample.dtype not in dtypes: continue
    if channel and sample.channels and not any(fnmatch(channel,c) for c in sample.channels): continue
    if sample.name in sampledict:
      LOG.throw(IOError,"Sample short names should be unique. Found two samples '%s'!\n\t%s\n\t%s"%(
                        sample.name,','.join(sampledict[sample.name].paths),','.join(sample.paths)))
    if 'skim' in channel and sample.dosplit: # split samples with multiple DAS dataset paths, and submit as separate jobs
      for subsample in sample.split():
        samples.append(subsample) # keep correspondence sample to one sample in DAS
    else:
      samples.append(sample)
    sampledict[sample.name] = sample
  return samples
  

def print_no_samples(dtype=[],filter=[],veto=[]):
  """Help function to print that no samples were found."""
  string  = ">>> Did not find any samples"
  if filter or veto or dtype:
    strings = [ ]
    if filter:
      strings.append("filters '%s'"%("', '".join(filter)))
    if veto:
      strings.append("vetoes '%s'"%("', '".join(veto)))
    if dtype and len(dtype)<3:
      strings.append("data types '%s'"%("', '".join(dtype)))
    string += " with "+', '.join(strings)
  print string
  
