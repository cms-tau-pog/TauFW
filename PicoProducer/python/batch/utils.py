# Author: Izaak Neutelings (May 2020)
import os, re, glob
import importlib
from TauFW.common.tools.file import ensureTFile
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.PicoProducer.batch import moddir
from TauFW.common.tools.log import Logger
from TauFW.common.tools.file import ensurefile, ensureTFile
from TauFW.common.tools.string import repkey
from TauFW.common.tools.math import partition_by_max, ceil, floor
from TauFW.common.tools.LoadingBar import LoadingBar
from TauFW.PicoProducer.storage.Sample import Sample
LOG = Logger('Storage')
evtsplitexp = re.compile(r"(.+\.root):(\d+):(\d+)$") # input file split by events


def chunkify_by_evts(fnames,maxevts,evenly=True,evtdict=None,verb=0):
  """Split list of files into chunks with total events per chunks less than given maximum,
  and update input fnames to bookkeep first event and maximum events.
  E.g. ['nano_1.root','nano_2.root','nano_3.root','nano_4.root']
        -> [ ['nano_1.root:0:1000'], ['nano_1.root:1000:1000'], # 'fname:firstevt:maxevts'
             ['nano_2.root','nano_3.root','nano_4.root'] ]
  """ 
  result   = [ ] # list of chunks
  nlarge   = { }
  nsmall   = { }
  ntot     = 0
  bar      = None # loading bar
  if verb<=0 and len(fnames)>=5:
    bar = LoadingBar(len(fnames),width=20,pre=">>> Checking number of events: ",counter=True,remove=True)
  elif verb>=4:
    print ">>> chunkify_by_evts: events per file:"
  for fname in fnames[:]:
    if evtsplitexp.match(fname): # already split; cannot be split again
      # TODO: add maxevts to ntot ?
      result.append([fname]) # do not split again, keep in single chunk
      continue
    if evtdict and fname in evtdict: # get number of events from sample's dictionary to speed up
      nevts = evtdict[fname]
      if verb>=4:
        print ">>> %10d %s (dict)"%(nevts,fname)
    else: # get number of events from file
      file  = ensureTFile(fname,'READ')
      nevts = file.Get('Events').GetEntries()
      file.Close()
      if isinstance(evtdict,dict):
        evtdict[fname] = nevts # store for possible later reuse (if same sample is submitted multiple times)
      if verb>=4:
        print ">>> %10d %s"%(nevts,fname)
    if nevts<maxevts: # split this large file into several chunks
      if nevts<=0:
        LOG.warning("chunkify_by_evts: File %r has %s<=0 events, not including..."%(fname,nevts))
      else:
        nsmall.setdefault(nevts,[ ]).append(fname)
    else: # don't split this small, group with others in chunks, if possible
      nlarge.setdefault(nevts,[ ]).append(fname)
      fnames.remove(fname)
    ntot += nevts
    if bar:
      bar.count("files")
  if verb>=1:
    print ">>> chunkify_by_evts: %d small files (<%d events) and %d large files (>=%d events)"%(
      len(nsmall),maxevts,len(nlarge),maxevts)
  for nevts in nlarge:
    for fname in nlarge[nevts]: # split large files into several chunks
      maxevts_ = maxevts
      if evenly: # split events evenly over chunks
        nchunks  = ceil(float(nevts)/maxevts)
        maxevts_ = int(ceil(nevts/nchunks)) # new maxevts per chunk
        if verb>=3:
          print ">>>   nevts/maxevts = %d/%d = %.2f => make %d chunks with max. %d events"%(
            nevts,maxevts,nevts/float(maxevts),nchunks,maxevts_)
      ifirst = 0 # first event to process in first chunk
      while ifirst<nevts:
        #if ifirst+maxevts_+1>=nevts: # if nevts%maxevts_!=0; index starts counting from 0
        #  maxevts_ = nevts - (nchunks-1)*maxevts_ # maxevts for the last chunk; use correct maxevts for bookkeeping ntot
        infname = "%s:%d:%d"%(fname,ifirst,maxevts_)
        fnames.append(infname) # update for book keeping
        result.append([infname])
        ifirst += maxevts_
  mylist = [ ]
  for nevts in nsmall:
    mylist.extend([nevts]*len(nsmall[nevts]))
  for part in partition_by_max(mylist,maxevts): # group small files into one chunk
    result.append([ ])
    for nevts in part:
      fname = nsmall[nevts][0]
      nsmall[nevts].remove(fname)
      result[-1].append(fname) #+":%d"%nevts)
  if verb>=4:
    print ">>> chunkify_by_evts: chunks = ["
    for chunk in result:
      print ">>>   %s"%(chunk)
    print ">>> ]"
  return ntot, result


def getbatch(arg,verb=0):
  """Get BatchSystem (subclass) instance and check if it exists."""
  if isinstance(arg,basestring):
    system = arg
  elif hasattr(arg,'batch'):
    system = arg.batch
  elif isinstance(arg,dict) and 'batch' in arg:
    system = arg[batch]
  else:
    raise IOError("Did not recognize argument",arg)
  modfile = os.path.join(moddir,system+".py")
  modpath = "TauFW.PicoProducer.batch.%s"%(system)
  assert os.path.isfile(modfile), "Did not find python module %s for batch system '%s'"%(modfile,system)
  module  = importlib.import_module(modpath)
  batch   = getattr(module,system)(verb=verb)
  return batch
  

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
    if jobcfgs:
      print ">>> getcfgsamples: Found job config:"
    else:
      print ">>> getcfgsamples: Found NO job configs %s"%(jobcfgnames)
  for cfgname in sorted(jobcfgs):
    if verb>=2:
      print ">>>   %s"%(cfgname)
    sample = Sample.loadjson(cfgname)
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
  
