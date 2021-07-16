#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.common.tools.utils import execute
from TauFW.common.tools.log import Logger, bold
from TauFW.PicoProducer.analysis.utils import ensuremodule
from TauFW.PicoProducer.storage.utils import getsamples, print_no_samples
os.chdir(GLOB.basedir)
CONFIG = GLOB.getconfig(verb=0)
LOG    = Logger()



###########
#   RUN   #
###########

def main_run(args):
  """Run given module locally."""
  if args.verbosity>=1:
    print ">>> main_run", args
  eras       = args.eras       # eras to loop over and run
  channels   = args.channels   # channels to loop over and run
  tag        = args.tag        # extra tag for output file
  outdir     = args.outdir     # output directory
  dtypes     = args.dtypes     # filter (only include) these sample types ('data','mc','embed')
  filters    = args.samples    # filter (only include) these samples (glob patterns)
  dasfilters = args.dasfilters # filter (only include) these das paths (glob patterns)
  vetoes     = args.vetoes     # exclude these sample (glob patterns)
  dasvetoes  = args.dasvetoes  # exclude these DAS paths (glob patterns)
  extraopts  = args.extraopts  # extra options for module (for all runs)
  prefetch   = args.prefetch   # copy input file first to local output directory
  maxevts    = args.maxevts    # maximum number of files (per sample, era, channel)
  dasfiles   = args.dasfiles   # explicitly process nanoAOD files stored on DAS (as opposed to local storage)
  userfiles  = args.infiles    # use these input files
  nfiles     = args.nfiles     # maximum number of files (per sample, era, channel)
  nsamples   = args.nsamples   # maximum number of samples (per era, channel)
  dryrun     = args.dryrun     # prepare and print command, without executing
  verbosity  = args.verbosity  # verbosity to print out what's going on under the hood
  preselect  = args.preselect  # extra selection string
  if len(filters)==0:
    filters = [None]
  
  # LOOP over ERAS
  if not eras:
    print ">>> Please specify a valid era (-y)."
  if not channels:
    print ">>> Please specify a valid channel (-c)."
  for era in eras:
    moddict = { } # save time by loading samples and get their files only once
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # MODULE & PROCESSOR
      skim = 'skim' in channel.lower()
      module, processor, procopts, extrachopts = getmodule(channel,extraopts)
      
      # VERBOSE
      if verbosity>=1:
        print '-'*80
        print ">>> Running %r"%(channel)
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %r"%('processor',processor)
        print ">>> %-12s = %r"%('procopts',procopts)
        print ">>> %-12s = %r"%('extrachopts',extrachopts)
        print ">>> %-12s = %r"%('prefetch',prefetch)
        print ">>> %-12s = %r"%('preselect',preselect)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
        print ">>> %-12s = %r"%('userfiles',userfiles)
        print ">>> %-12s = %r"%('outdir',outdir)
      
      # LOOP over FILTERS
      samples = [ ]
      for filter in filters:
        filters_ = [filter] if filter else [ ]
        if verbosity>=2:
          print ">>> Checking filters=%s, vetoes=%s, dtypes=%s..."%(filters_,vetoes,dtypes)
        
        # GET SAMPLES
        if not userfiles and (filters_ or vetoes or dtypes):
          LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
          samples_ = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters_,veto=vetoes,
                                dasfilter=dasfilters,dasveto=dasvetoes,moddict=moddict,verb=verbosity)
          for sample in samples_[:]:
            if sample in samples: # avoid duplicates
              samples_.remove(sample)
          if nsamples>0: # limit number of samples to maximum nsamples
            samples_ = samples_[:nsamples]
          samples.extend(samples_)
      if not sample:
        samples = [None]
        if not userfiles and (filters_ or vetoes or dtypes):
          print_no_samples(dtypes,filters_,vetoes)
      if verbosity>=1:
        print ">>> %-12s = %r"%('samples',samples)
        print '-'*80
      
      # LOOP over SAMPLES
      for sample in samples:
        if sample:
          print ">>> %s"%(bold(sample.name))
          if verbosity>=1:
            for path in sample.paths:
              print ">>> %s"%(bold(path))
        
        # SETTINGS
        dtype      = None
        extraopts_ = extrachopts[:] # extra options for module (for this channel & sample)
        if sample:
          filetag  = "_%s_%s_%s%s"%(channel,era,sample.name,tag)
          if sample.extraopts:
            extraopts_.extend(sample.extraopts)
        else:
          filetag  = "_%s_%s%s"%(channel,era,tag)
        if verbosity>=1:
          print ">>> %-12s = %s"%('sample',sample)
          print ">>> %-12s = %r"%('filetag',filetag) # postfix
          print ">>> %-12s = %s"%('extraopts',extraopts_)
        
        # GET FILES
        infiles = [ ]
        if userfiles:
          infiles = userfiles[:]
        elif sample:
          nevents = 0
          infiles = sample.getfiles(das=dasfiles,verb=verbosity)
          dtype   = sample.dtype
          if nfiles>0:
            infiles = infiles[:nfiles]
          if verbosity==1:
            print ">>> %-12s = %r"%('dtype',dtype)
            print ">>> %-12s = %s"%('nfiles',len(infiles))
            print ">>> %-12s = [ "%('infiles')
            for file in infiles:
              print ">>>   %r"%file
            print ">>> ]"
        
        # RUN
        runcmd = processor
        if procopts:
          runcmd += " %s"%(procopts)
        if skim:
          runcmd += " -y %s -o %s"%(era,outdir)
          if preselect:
            runcmd += " --preselect '%s'"%(preselect)
        ###elif 'test' in channel:
        ###  runcmd += " -o %s"%(outdir)
        else: # analysis
          runcmd += " -y %s -c %s -M %s -o %s"%(era,channel,module,outdir)
        if dtype:
          runcmd += " -d %r"%(dtype)
        if filetag:
          runcmd += " -t %r"%(filetag) # postfix
        if maxevts:
          runcmd += " -m %s"%(maxevts)
        if infiles:
          runcmd += " -i %s"%(' '.join(infiles))
        if prefetch:
          runcmd += " -p"
        if extraopts_:
          runcmd += " --opt '%s'"%("' '".join(extraopts_))
        #elif nfiles:
        #  runcmd += " --nfiles %s"%(nfiles)
        print ">>> Executing: "+bold(runcmd)
        if not dryrun:
          #execute(runcmd,dry=dryrun,verb=verbosity+1) # real-time print out does not work well with python script 
          os.system(runcmd)
        print
      

      
##################
#   GET MODULE   #
##################

def getmodule(channel,extraopts):
  """Help function to get the module and processor."""
  LOG.insist(channel in CONFIG.channels,"Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels))
  module      = CONFIG.channels[channel]
  procopts    = "" # extra options for processor
  extrachopts = extraopts[:] # extra options for module (per channel)
  if 'skim' in channel.lower():
    parts     = module.split(' ') # "PROCESSOR [--FLAG[=VALUE] ...]"
    processor = parts[0]
    procopts  = ' '.join(parts[1:])
  ###elif channel=='test':
  ###  processor = module
  else:
    parts     = module.split(' ') # "MODULE [KEY=VALUE ...]"
    processor = "picojob.py"
    module    = parts[0]
    ensuremodule(module) # sanity check
    extrachopts.extend(parts[1:])
  procpath  = os.path.join("python/processors",processor)
  if not os.path.isfile(procpath):
    LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
  processor = os.path.abspath(procpath)
  return module, processor, procopts, extrachopts
  
