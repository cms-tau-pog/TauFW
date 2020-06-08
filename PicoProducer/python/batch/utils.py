# Author: Izaak Neutelings (May 2020)
import os, glob
import importlib
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.PicoProducer.batch import moddir
from TauFW.PicoProducer.tools.log import Logger
from TauFW.PicoProducer.tools.file import ensurefile
from TauFW.PicoProducer.tools.utils import repkey
from TauFW.PicoProducer.storage.Sample import Sample
LOG = Logger('Storage')


def getbatch(arg,verb=0):
  """Get BatchSystem (subclass) instance and check if it exists."""
  if isinstance(arg,basestring):
    system = arg
  elif hasattr(arg,'batch'):
    system = arg.batch
  else:
    raise IOError("Did not recognize argument",arg)
  modfile = os.path.join(moddir,system+".py")
  modpath = "TauFW.PicoProducer.batch.%s"%(system)
  assert os.path.isfile(modfile), "Did not find python module %s for batch system '%s'"%(modfile,system)
  module  = importlib.import_module(modpath)
  batch   = getattr(module,system)(verb=verb)
  return batch
  

def getsamples(era,channel="",tag="",dtype=[],filter=[],veto=[],moddict={},verb=0):
  """Help function to get samples from a sample list and filter if needed."""
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
  for sample in samplelist:
    if filters and not sample.match(filters,verb): continue
    if vetoes and sample.match(vetoes,verb): continue
    if dtypes and sample.dtype not in dtypes: continue
    if sample.name in sampledict:
      LOG.throw(IOError,"Sample short names should be unique. Found two samples '%s'!\n\t%s\n\t%s"%(
                    sample.name,','.join(sampledict[sample.name].paths),','.join(sample.paths)))
    if 'skim' in channel and len(sample.paths)>=2:
      for subsample in sample.split():
        samples.append(subsample) # keep correspondence sample to one sample in DAS
    else:
      samples.append(sample)
    sampledict[sample.name] = sample
  return samples
  

def getcfgsamples(jobcfgnames,filter=[ ],veto=[ ],dtype=[ ],verb=0):
  """Help function to get samples from a job configuration file.
  Return list of Sample objects."""
  import glob
  filters = filter if isinstance(filter,list) else [filter]
  vetoes  = veto   if isinstance(veto,list)   else [veto]
  dtypes  = dtype  if isinstance(dtype,list)  else [dtype]
  jobcfgs = glob.glob(jobcfgnames)
  
  samples = [ ]
  if verb>=2:
    print ">>> getcfgsamples: Found job config:"
  for cfgname in sorted(jobcfgs):
    if verb>=2:
      print ">>>   %s"%(cfgname)
    sample = Sample.loadJSON(cfgname)
    if filters and not sample.match(filters,verb): continue
    if vetoes and sample.match(vetoes,verb): continue
    if sample.dtype not in dtypes: continue
    for i, osample in enumerate(samples):
      if sample.name!=osample.name: continue
      if sample.paths!=osample.paths: continue
      if sample.channels[0] not in osample.channels: continue
      if sample.subtry>osample.subtry: # ensure last job (re)submission
        samples[samples.index(osample)] = sample # replace
      break
    else: # if no break
      samples.append(sample)
  return samples
  
