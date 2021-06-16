#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, sys, re, glob, json
from datetime import datetime
from collections import OrderedDict
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.common.tools.file import ensuredir, ensurefile, ensureinit, getline
from TauFW.common.tools.utils import execute, chunkify, repkey, alphanum_key, lreplace, rreplace
from TauFW.common.tools.log import Logger, color, bold
from TauFW.PicoProducer.analysis.utils import getmodule, ensuremodule
from TauFW.PicoProducer.batch.utils import getbatch, getcfgsamples, chunkify_by_evts, evtsplitexp
from TauFW.PicoProducer.storage.utils import getstorage, getsamples, isvalid, print_no_samples
from argparse import ArgumentParser
os.chdir(GLOB.basedir)
CONFIG = GLOB.getconfig(verb=0)
LOG    = Logger()


###############
#   INSTALL   #
###############

def main_install(args):
  """Install producer."""
  # TODO:
  #  - guess location (lxplus/PSI/...)
  #  - set defaults of config file
  #  - outside CMSSW: create symlinks for standalone
  if args.verbosity>=1:
    print ">>> main_install", args
  verbosity = args.verbosity
  


###########
#   LIST   #
###########

def main_list(args):
  """List contents of configuration for those lazy to do 'cat config/config.json'."""
  if args.verbosity>=1:
    print ">>> main_list", args
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  print ">>> Configuration %s:"%(cfgname)
  for variable, value in CONFIG.iteritems():
    variable = "'"+color(variable)+"'"
    if isinstance(value,dict):
      print ">>>  %s:"%(variable)
      for key, item in value.iteritems():
        if isinstance(item,basestring): item = str(item)
        print ">>>    %-12r -> %r"%(str(key),str(item))
    else:
      if isinstance(value,basestring): value = str(value)
      print ">>>  %-24s = %r"%(variable,value)
  


###########
#   GET   #
###########

def main_get(args):
  """Get information of given variable in configuration or samples."""
  if args.verbosity>=1:
    print ">>> main_get", args
  variable   = args.variable
  eras       = args.eras
  channels   = args.channels or [""]
  dtypes     = args.dtypes
  filters    = args.samples
  vetoes     = args.vetoes
  inclurl    = args.inclurl    # include URL in filelist
  checkdas   = args.checkdas or args.dasfiles # check file list in DAS
  checklocal = args.checklocal # check nevents in local files
  split      = args.split # split samples with multiple DAS dataset paths
  limit      = args.limit
  writedir   = args.write      # write sample file list to text file
  tag        = args.tag
  verbosity  = args.verbosity
  getnevts   = variable in ['nevents','nevts']
  cfgname    = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('variable',variable)
    print ">>> %-14s = %s"%('eras',eras)
    print ">>> %-14s = %s"%('channels',channels)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  # LIST SAMPLES
  if variable=='samples':
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        if channel:
          print ">>> Getting file list for era %r, channel %r"%(era,channel)
        else:
          print ">>> Getting file list for era %r"%(era)
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,verb=verbosity)
        if not samples:
          LOG.warning("No samples found for era %r."%(era))
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>>   %s"%(path)
  
  # LIST SAMPLE FILES
  elif variable in ['files','nevents','nevts']:
    
    # LOOP over ERAS & CHANNELS
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        target = "file list" if variable=='files' else "nevents"
        if channel:
          print ">>> Getting %s for era %r, channel %r"%(target,era,channel)
        else:
          print ">>> Getting %s for era %r"%(target,era)
        print ">>> "
        
        # GET SAMPLES
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,split=split,verb=verbosity)
        
        # LOOP over SAMPLES
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>> %s"%(bold(path))
          if getnevts or checkdas or checklocal:
            nevents = sample.getnevents(das=(not checklocal),verb=verbosity+1)
            storage = sample.storage.__class__.__name__ if checklocal else "DAS"
            print ">>>   %-7s = %s (%s)"%('nevents',nevents,storage)
          if variable=='files':
            infiles = sample.getfiles(das=checkdas,url=inclurl,limit=limit,verb=verbosity+1)
            print ">>>   %-7s = %r"%('channel',channel)
            print ">>>   %-7s = %r"%('url',sample.url)
            print ">>>   %-7s = %r"%('postfix',sample.postfix)
            print ">>>   %-7s = %s"%('nfiles',len(infiles))
            print ">>>   %-7s = [ "%('infiles')
            for file in infiles:
              print ">>>     %r"%file
            print ">>>   ]"
          print ">>> "
          if writedir: # write files to text files
            flistname = repkey(writedir,ERA=era,GROUP=sample.group,SAMPLE=sample.name,TAG=tag)
            print ">>> Write list to %r..."%(flistname)
            sample.writefiles(flistname,nevts=getnevts)
  
  # CONFIGURATION
  else:
    if variable in CONFIG:
      print ">>> Configuration of %r: %s"%(variable,color(CONFIG[variable]))
    else:
      print ">>> Did not find %r in the configuration"%(variable)
  


#############
#   WRITE   #
#############

def main_write(args):
  """Get information of given variable in configuration or samples."""
  if args.verbosity>=1:
    print ">>> main_write", args
  listname   = args.listname   # write sample file list to text file
  eras       = args.eras
  channels   = args.channels or [""]
  dtypes     = args.dtypes
  filters    = args.samples
  vetoes     = args.vetoes
  checkdas   = args.checkdas or args.dasfiles # check file list in DAS
  split      = args.split # split samples with multiple DAS dataset paths
  retries    = args.retries
  getnevts   = args.getnevts # check nevents in local files
  verbosity  = args.verbosity
  cfgname    = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('listname',listname)
    print ">>> %-14s = %s"%('getnevts',getnevts)
    print ">>> %-14s = %s"%('eras',eras)
    print ">>> %-14s = %s"%('channels',channels)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  # LOOP over ERAS & CHANNELS
  if not eras:
    LOG.warning("Please specify an era to get a sample for.")
  for era in eras:
    for channel in channels:
      info = ">>> Getting file list for era %r"%(era)
      if channel:
        info += ", channel %r"%(channel)
      print info
      print ">>> "
      
      LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
      samples0 = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,split=split,verb=verbosity)
      sampleset = [samples0]
      for retry in range(retries):
        sampleset.append([ ]) # list for retries
      
      # LOOP over SAMPLES
      for retry, samples in enumerate(sampleset):
        if not samples:
          break
        if retry>0 and len(samples0)>1:
          if retries>=2:
            print ">>> Retry %d/%d: %d/%d samples...\n>>>"%(retry,retries,len(samples),len(samples0))
          else:
            print ">>> Trying again %d/%d samples...\n>>>"%(len(samples),len(samples0))
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          sample.filelist = None # do not load from existing text file
          for path in sample.paths:
            print ">>> %s"%(bold(path))
          #infiles = sample.getfiles(das=checkdas,url=inclurl,limit=limit,verb=verbosity+1)
          flistname = repkey(listname,ERA=era,GROUP=sample.group,SAMPLE=sample.name) #,TAG=tag
          try:
            sample.writefiles(flistname,nevts=getnevts,das=checkdas,refresh=checkdas,verb=verbosity)
          except IOError as err: # one of the ROOT file could not be opened
            print "IOError: "+err.message
            if retry<retries and sample not in sampleset[retry+1]: # try again after the others
              print ">>> Will try again..."
              sampleset[retry+1].append(sample)
          print ">>> "
  


###########
#   SET   #
###########

def main_set(args):
  """Set variables in the config file."""
  if args.verbosity>=1:
    print ">>> main_set", args
  variable  = args.variable
  key       = args.key # 'channel' or 'era'
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if key: # redirect 'channel' and 'era' keys to main_link
    args.subcommand = variable
    return main_link(args)
  elif variable in ['channel','era']:
      LOG.throw(IOError,"Variable '%s' is reserved for dictionaries!"%(variable))
  if verbosity>=1:
    print '-'*80
  print ">>> Setting variable '%s' to '%s' config"%(color(variable),value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if variable=='all':
    if 'default' in value:
      GLOB.setdefaultconfig(verb=verb)
    else:
      LOG.warning("Did not recognize value '%s'. Did you mean 'default'?"%(value))
  elif variable in ['nfilesperjob','maxevtsperjob']:
    CONFIG[variable] = int(value)
    CONFIG.write()
  else:
    CONFIG[variable] = value
    CONFIG.write()
  


############
#   LINK   #
############

def main_link(args):
  """Link channels or eras in the config file."""
  if args.verbosity>=1:
    print ">>> main_link", args
  variable  = args.subcommand
  varkey    = variable+'s'
  key       = args.key
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  print ">>> Linking %s '%s' to '%s' in the configuration..."%(variable,color(key),value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('key',key)
    print ">>> %-14s = %s"%('value',value)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  
  # SANITY CHECKS
  if varkey not in CONFIG:
    CONFIG[varkey] = { }
  LOG.insist(isinstance(CONFIG[varkey],dict),"%s in %s has to be a dictionary"%(varkey,cfgname))
  oldval = value
  for char in '/\,:;!?\'" ':
    if char in key:
      LOG.throw(IOError,"Given key '%s', but keys cannot contain any of these characters: %s"%(key,char))
  if varkey=='channels':
    if 'skim' in key.lower(): #or 'test' in key:
      parts  = value.split(' ') # "PROCESSOR [--FLAG[=VALUE] ...]"
      script = os.path.basename(parts[0]) # separate script from options
      ensurefile("python/processors",script)
      value  = ' '.join([script]+parts[1:])
    else:
      parts  = value.split(' ') # "MODULE [KEY=VALUE ...]"
      module = parts[0]
      LOG.insist(all('=' in o for o in parts[1:]),"All extra module options should be of format KEY=VALUE!")
      if 'python/analysis/' in module: # useful for tab completion
        module = module.split('python/analysis/')[-1].replace('/','.')
      module = rreplace(module,'.py')
      path   = os.path.join('python/analysis/','/'.join(module.split('.')[:-1]))
      ensureinit(path,by="pico.py")
      ensuremodule(module)
      value  = ' '.join([module]+parts[1:])
  elif varkey=='eras':
    if 'samples/' in value: # useful for tab completion
      value = ''.join(value.split('samples/')[1:])
    path = os.path.join("samples",repkey(value,ERA='*',CHANNEL='*',TAG='*'))
    LOG.insist(glob.glob(path),"Did not find any sample lists '%s'"%(path))
    ensureinit(os.path.dirname(path),by="pico.py")
  if value!=oldval:
    print ">>> Converted '%s' to '%s'"%(oldval,value)
  CONFIG[varkey][key] = value
  CONFIG.write()
  


##############
#   REMOVE   #
##############

def main_rm(args):
  """Remove variable from the config file."""
  if args.verbosity>=1:
    print ">>> main_rm", args
  variable  = args.variable
  key       = args.key # 'channel' or 'era'
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  if key:
    print ">>> Removing %s '%s' from the configuration..."%(variable,color(key))
  else:
    print ">>> Removing variable '%s' from the configuration..."%(color(variable))
  if verbosity>=1:
    print ">>> %-14s = %s"%('variable',variable)
    print ">>> %-14s = %s"%('key',key)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if key: # redirect 'channel' and 'era' keys to main_link
    variable = variable+'s'
    if variable in CONFIG:
      if key in CONFIG[variable]:
        CONFIG[variable].pop(key,None)
        CONFIG.write()
      else:
        print ">>> %s '%s' not in the configuration. Nothing to remove..."%(variable.capitalize(),key)
    else:
      print ">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable)
  else:
    if variable in CONFIG:
      CONFIG.pop(variable)
      CONFIG.write()
    else:
      print ">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable)
  


###########
#   RUN   #
###########

def main_run(args):
  """Run given module locally."""
  if args.verbosity>=1:
    print ">>> main_run", args
  eras      = args.eras      # eras to loop over and run
  channels  = args.channels  # channels to loop over and run
  tag       = args.tag       # extra tag for output file
  outdir    = args.outdir
  dtypes    = args.dtypes    # filter (only include) these sample types ('data','mc','embed')
  filters   = args.samples   # filter (only include) these samples (glob patterns)
  vetoes    = args.vetoes    # exclude these sample (glob patterns)
  extraopts = args.extraopts # extra options for module (for all runs)
  prefetch  = args.prefetch  # copy input file first to local output directory
  maxevts   = args.maxevts   # maximum number of files (per sample, era, channel)
  dasfiles  = args.dasfiles  # explicitly process nanoAOD files stored on DAS (as opposed to local storage)
  userfiles = args.infiles   # use these input files
  nfiles    = args.nfiles    # maximum number of files (per sample, era, channel)
  nsamples  = args.nsamples  # maximum number of samples (per era, channel)
  dryrun    = args.dryrun    # prepare and print command, without executing
  verbosity = args.verbosity
  preselect = args.preselect # extra selection string
  
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
      for filter in filters:
        filters_ = [filter]
        
        # GET SAMPLES
        if not userfiles and (filters_ or vetoes or dtypes):
          LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
          samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters_,veto=vetoes,moddict=moddict,verb=verbosity)
          if nsamples>0:
            samples = samples[:nsamples]
          if not samples:
            print_no_samples(dtypes,filters_,vetoes)
        else:
          samples = [None]
        if verbosity>=2:
          print ">>> %-12s = %r"%('samples',samples)
        if verbosity>=1:
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
          if verbosity==1:
            print '-'*80
          
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
  


####################
#   PREPARE JOBS   #
####################

def preparejobs(args):
  """Help function for (re)submission to iterate over samples per given channel and era
  and prepare job config and list."""
  if args.verbosity>=1:
    print ">>> preparejobs", args
  
  resubmit     = args.subcommand=='resubmit'
  eras         = args.eras
  channels     = args.channels
  tag          = args.tag
  dtypes       = args.dtypes       # filter (only include) these sample types ('data','mc','embed')
  filters      = args.samples      # filter (only include) these samples (glob patterns)
  vetoes       = args.vetoes       # exclude these sample (glob patterns)
  dasfiles     = args.dasfiles     # explicitly process nanoAOD files stored on DAS (as opposed to local storage)
  checkdas     = args.checkdas     # look up number of events in DAS and compare to processed events in job output
  checkqueue   = args.checkqueue   # check job status to speed up if batch is slow: 0 (no check), 1 (check once, fast), -1 (check every job, slow, default)
  checkevts    = args.checkevts    # validate output files and counts events (default, but slow)
  checkexpevts = args.checkexpevts # compare actual vs. processed number of events
  extraopts    = args.extraopts    # extra options for module (for all runs)
  prefetch     = args.prefetch     # copy input file first to local output directory
  preselect    = args.preselect    # preselection string for post-processing
  nfilesperjob = args.nfilesperjob # split jobs based on number of files
  maxevts      = args.maxevts      # split jobs based on events
  split_nfpj   = args.split_nfpj   # split failed (file-based) chunks into even smaller chunks
  testrun      = args.testrun      # only run a few test jobs
  queue        = args.queue        # queue option for the batch system (job flavor for HTCondor)
  force        = args.force        # force submission, even if old job output exists
  prompt       = args.prompt       # ask user for confirmation
  tmpdir       = args.tmpdir or CONFIG.get('tmpskimdir',None) # temporary dir for creating skimmed file before copying to outdir
  verbosity    = args.verbosity
  jobs         = [ ]
  
  # LOOP over ERAS
  for era in eras:
    moddict = { } # save time by loading samples and get their file list only once
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # MODULE & PROCESSOR
      skim = 'skim' in channel.lower()
      module, processor, procopts, extrachopts = getmodule(channel,extraopts)
      if verbosity>=1:
        print '-'*80
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('processor',processor)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %r"%('procopts',procopts)
        print ">>> %-12s = %r"%('extrachopts',extrachopts)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
      
      # GET SAMPLES
      jobdirformat = CONFIG.jobdir # for job config & log files
      outdirformat = CONFIG.nanodir if skim else CONFIG.outdir # for job output
      jobdir_      = ""
      jobcfgs      = ""
      if resubmit: # get samples from existing job config files
        # TODO: allow user to resubmit given config file
        jobdir_ = repkey(jobdirformat,ERA=era,SAMPLE='*',CHANNEL=channel,TAG=tag)
        jobcfgs = repkey(os.path.join(jobdir_,"config/jobconfig_$SAMPLE$TAG_try[0-9]*.json"),
                         ERA=era,SAMPLE='*',CHANNEL=channel,TAG=tag)
        if verbosity>=2:
          print ">>> %-12s = %s"%('cwd',os.getcwd())
          print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      else: # get samples from sample list
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,moddict=moddict,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      if testrun:
        samples = samples[:2] # run at most two samples
      
      # LOOP over SAMPLES
      found  = len(samples)>=0
      failed = [ ] # failed samples
      for sample in samples:
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # DIRECTORIES
        subtry     = sample.subtry+1 if resubmit else 1
        jobids     = sample.jobcfg.get('jobids',[ ])
        queue_     = queue or sample.jobcfg.get('queue',None)
        prefetch_  = sample.jobcfg.get('prefetch',prefetch) or prefetch # if resubmit: reuse old setting, or override by user
        dtype      = sample.dtype
        postfix    = "_%s%s"%(channel,tag)
        jobtag     = "%s_try%d"%(postfix,subtry)
        jobname    = "%s%s_%s%s"%(sample.name,postfix,era,"_try%d"%subtry if subtry>1 else "")
        extraopts_ = extrachopts[:] # extra options for module (for this channel & sample)
        if sample.extraopts:
          extraopts_.extend(sample.extraopts)
        nfilesperjob_ = nfilesperjob if nfilesperjob>0 else sample.nfilesperjob if sample.nfilesperjob>0 else CONFIG.nfilesperjob # priority: USER > SAMPLE > CONFIG
        maxevts_   = maxevts if maxevts>0 else sample.maxevts if sample.maxevts>0 else CONFIG.maxevtsperjob # priority: USER > SAMPLE > CONFIG
        if split_nfpj>1: # divide nfilesperjob by split_nfpj
          nfilesperjob_ = int(max(1,nfilesperjob_/float(split_nfpj)))
        elif resubmit and maxevts<=0: # reuse previous maxevts settings if maxevts not set by user
          maxevts_ = sample.jobcfg.get('maxevts',maxevts_)
          if nfilesperjob<=0: # reuse previous nfilesperjob settings if nfilesperjob not set by user
            nfilesperjob_ = sample.jobcfg.get('nfilesperjob',nfilesperjob_)
        daspath    = sample.paths[0].strip('/')
        outdir     = repkey(outdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                         DAS=daspath,PATH=daspath,GROUP=sample.group)
        jobdir     = ensuredir(repkey(jobdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                   DAS=daspath,PATH=daspath,GROUP=sample.group))
        cfgdir     = ensuredir(jobdir,"config")
        logdir     = ensuredir(jobdir,"log")
        cfgname    = "%s/jobconfig%s.json"%(cfgdir,jobtag)
        joblist    = '%s/jobarglist%s.txt'%(cfgdir,jobtag)
        if verbosity==1:
          print ">>> %-12s = %s"%('cfgname',cfgname)
          print ">>> %-12s = %s"%('joblist',joblist)
        elif verbosity>=2:
          print '-'*80
          print ">>> Preparing job %ssubmission for '%s'"%("re" if resubmit else "",sample.name)
          print ">>> %-12s = %r"%('processor',processor)
          print ">>> %-12s = %r"%('dtype',dtype)
          print ">>> %-12s = %r"%('jobname',jobname)
          print ">>> %-12s = %r"%('jobtag',jobtag)
          print ">>> %-12s = %r"%('postfix',postfix)
          print ">>> %-12s = %r"%('outdir',outdir)
          print ">>> %-12s = %r"%('extraopts',extraopts_)
          print ">>> %-12s = %r"%('prefetch',prefetch_)
          print ">>> %-12s = %r"%('preselect',preselect)
          print ">>> %-12s = %r"%('cfgdir',cfgdir)
          print ">>> %-12s = %r"%('logdir',logdir)
          print ">>> %-12s = %r"%('tmpdir',tmpdir)
          print ">>> %-12s = %r"%('cfgname',cfgname)
          print ">>> %-12s = %r"%('joblist',joblist)
          print ">>> %-12s = %s"%('try',subtry)
          print ">>> %-12s = %r"%('jobids',jobids)
          print ">>> %-12s = %r"%('queue',queue_)
        
        # CHECKS
        if os.path.isfile(cfgname):
          # TODO: check for running jobs ?
          skip = False
          if force:
            LOG.warning("Job configuration %r already exists and will be overwritten! "%(cfgname)+
                        "Please beware of conflicting job output!")
          elif args.prompt:
            LOG.warning("Job configuration %r already exists and might cause conflicting job output!"%(cfgname))
            while True:
              submit = raw_input(">>> Submit anyway? [y/n] "%(nchunks))
              if 'f' in submit.lower(): # submit this job, and stop asking
                print ">>> Force all."
                force = True; skip = True; break
              elif 'y' in submit.lower(): # submit this job
                print ">>> Continue submission..."
                skip = True; break
              elif 'n' in submit.lower(): # do not submit this job
                print ">>> Not submitting."
                break
              else:
                print ">>> '%s' is not a valid answer, please choose y/n."%submit
          else:
            skip = True
            LOG.warning("Job configuration %r already exists and might cause conflicting job output! "%(cfgname)+
                        "To submit anyway, please use the --force flag")
          if skip: # do not submit this job
            failed.append(sample)
            print ""
            continue
        if not resubmit: # check for existing jobss
          cfgpattern = re.sub(r"(?<=try)\d+(?=.json$)",r"*",cfgname)
          cfgnames   = [f for f in glob.glob(cfgpattern) if not f.endswith("_try1.json")]
          if cfgnames:
            LOG.warning("Job configurations for resubmission already exists! This can cause conflicting job output!"+
              "If you are sure you want to submit from scratch, please remove these files:\n>>>   "+"\n>>>   ".join(cfgnames))
        storage = getstorage(outdir,verb=verbosity,ensure=True)
        
        # GET FILES
        nevents = 0
        if resubmit: # resubmission
          if checkqueue==1 and not jobs: # check jobs only once to speed up performance
            batch = getbatch(CONFIG,verb=verbosity)
            jobs  = batch.jobs(verb=verbosity-1)
          infiles, chunkdict = checkchunks(sample,channel=channel,tag=tag,jobs=jobs,checkqueue=checkqueue,
                                           checkevts=checkevts,checkexpevts=checkexpevts,das=checkdas,verb=verbosity)[:2]
          nevents = sample.jobcfg['nevents'] # updated in checkchunks
        else: # first-time submission
          infiles   = sample.getfiles(das=dasfiles,verb=verbosity-1)
          if checkdas:
            nevents = sample.getnevents()
          chunkdict = { }
        if testrun:
          infiles = infiles[:4] # only run four files per sample
        if verbosity==1:
          print ">>> %-12s = %s"%('maxevts',maxevts_)
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
        elif verbosity>=2:
          print ">>> %-12s = %s"%('maxevts',maxevts_)
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
          print ">>> %-12s = [ "%('infiles')
          for file in infiles:
            print ">>>   %r"%file
          print ">>> ]"
        
        # CHUNKS - partition/split list 
        infiles.sort() # to have consistent order with resubmission
        chunks    = [ ] # chunk indices
        if maxevts_>1:
          if verbosity>=1:
            print ">>> Preparing jobs with chunks split by number of events..."
            
          try:
            ntot, fchunks = chunkify_by_evts(infiles,maxevts_,evtdict=sample.filenevts,verb=verbosity) # list of file chunks split by events
            if nevents<=0 and not resubmit:
              nevents = ntot
          except IOError as err: # capture if opening files fail
            print "IOError: "+err.message
            LOG.warning("Skipping submission...")
            failed.append(sample)
            print ""
            continue # ignore this submission
          if testrun:
            fchunks = fchunks[:4]
        else:
          if verbosity>=1:
            print ">>> Preparing jobs with chunks split by number of files..."
          fchunks = chunkify(infiles,nfilesperjob_) # list of file chunks split by number of files
        nfiles    = len(infiles)
        nchunks   = len(fchunks)
        if verbosity>=1:
          print ">>> %-12s = %s"%('nchunks',nchunks)
        if verbosity>=2:
          print ">>> %-12s = %s"%('nevents',nevents)
          print '-'*80
        
        # WRITE JOB LIST with arguments per job
        if args.verbosity>=1:
          print ">>> Creating job list %s..."%(joblist)
        if fchunks:
          with open(joblist,'w') as listfile:
            ichunk = 0
            for fchunk in fchunks:
              while ichunk in chunkdict:
                ichunk   += 1 # allows for different nfilesperjob on resubmission
                continue
              evtmatch    = evtsplitexp.match(fchunk[0]) # $fname:$firstevt:$maxevts
              if evtmatch:
                LOG.insist(len(fchunk)==1,"Chunks of event-split files can only have one input file: %s"%(fchunk))
                jobfiles  = evtmatch.group(1) # input file
                firstevt  = int(evtmatch.group(2))
                maxevts__ = int(evtmatch.group(3)) # limit number of events
              else:
                jobfiles  = ' '.join(fchunk) # list of input files
                firstevt  = -1
                maxevts__ = -1 # do not limit number of events
              filetag     = postfix
              if not skim:
                filetag  += "_%d"%(ichunk)
              elif firstevt>=0:
                filetag  += "_%d"%(firstevt/maxevts__)
              jobcmd      = processor
              if procopts:
                jobcmd   += " %s"%(procopts)
              if skim:
                jobcmd   += " -y %s -d '%s' -t %s --copydir %s"%(era,dtype,filetag,outdir)
                if tmpdir:
                  jobcmd += " -o %s"%(tmpdir) # temporary file for job output before copying
              ###elif channel=='test':
              ###  jobcmd += " -o %s -t %s -i %s"%(outdir,filetag)
              else:
                jobcmd   += " -y %s -d %r -c %s -M %s --copydir %s -t %s"%(era,dtype,channel,module,outdir,filetag)
              if prefetch_:
                jobcmd   += " -p"
              if preselect and skim:
                jobcmd   += " --preselect '%s'"%(preselect)
              if firstevt>=0:
                jobcmd   += " --firstevt %d"%(firstevt) # start at this entry (for event-based splitting)
              if testrun: # override maxevts
                jobcmd   += " -m %d"%(testrun) # process a limited amount of events for test jobs
              elif maxevts__>0:
                jobcmd   += " -m %d"%(maxevts__) # process a limited amount of events for event-based splitting
              if extraopts_:
                jobcmd   += " --opt '%s'"%("' '".join(extraopts_))
              jobcmd     += " -i %s"%(jobfiles) # add last
              if args.verbosity>=1:
                print ">>> chunk=%d, jobcmd=%r"%(ichunk,jobcmd)
              listfile.write(jobcmd+'\n')
              chunkdict[ichunk] = fchunk
              chunks.append(ichunk)
        
        # JSON CONFIG
        jobcfg = OrderedDict([
          ('time',str(datetime.now())),
          ('group',sample.group), ('paths',sample.paths), ('name',sample.name), ('nevents',nevents),
          ('dtype',dtype),        ('channel',channel),    ('module',module),    ('extraopts',extraopts_),
          ('jobname',jobname),    ('jobtag',jobtag),      ('tag',tag),          ('postfix',postfix),
          ('try',subtry),         ('queue',queue_),       ('jobids',jobids),    ('prefetch',prefetch_),
          ('outdir',outdir),      ('jobdir',jobdir),      ('cfgdir',cfgdir),    ('logdir',logdir),
          ('cfgname',cfgname),    ('joblist',joblist),    ('maxevts',maxevts_),
          ('nfiles',nfiles),      ('files',infiles),      ('nfilesperjob',nfilesperjob_), #('nchunks',nchunks),
          ('nchunks',nchunks),    ('chunks',chunks),      ('chunkdict',chunkdict),
          ('filenevts',sample.filenevts),
        ])
        
        # YIELD
        yield jobcfg
        print
      
      if not found:
        print_no_samples(dtypes,filters,vetoes,jobdir_,jobcfgs)
      elif failed and len(failed)!=len(samples):
        print ">>> %d/%d samples failed: %s\n"%(len(failed),len(samples),', '.join(s.name for s in failed))
    


##################
#   CHECK JOBS   #
##################

def checkchunks(sample,**kwargs):
  """Help function to check jobs status: success, pending, failed or missing.
  Return list of files to be resubmitted, and a dictionary between chunk index and input files."""
  outdir       = kwargs.get('outdir',       None  )
  channel      = kwargs.get('channel',      None  )
  tag          = kwargs.get('tag',          None  )
  checkqueue   = kwargs.get('checkqueue',   -1    ) # check queue of batch system for pending jobs
  checkevts    = kwargs.get('checkevts',    True  ) # validate output file & count events (slow, default)
  checkexpevts = kwargs.get('checkexpevts', False ) # compare actual to expected number of processed events
  pendjobs     = kwargs.get('jobs',         [ ]   )
  checkdas     = kwargs.get('das',          True  ) # check number of events from DAS
  showlogs     = kwargs.get('showlogs',     False ) # print log files of failed jobs
  verbosity    = kwargs.get('verb',         0     )
  oldjobcfg    = sample.jobcfg # job config from last job
  oldcfgname   = oldjobcfg['config']
  chunkdict    = oldjobcfg['chunkdict'] # filenames
  jobids       = oldjobcfg['jobids']
  joblist      = oldjobcfg['joblist']
  postfix      = oldjobcfg['postfix']
  logdir       = oldjobcfg['logdir']
  nfilesperjob = oldjobcfg['nfilesperjob']
  filenevts    = sample.filenevts
  if outdir==None:
    outdir     = oldjobcfg['outdir']
  storage      = getstorage(outdir,ensure=True) # StorageElement instance of output directory
  if channel==None:
    channel    = oldjobcfg['channel']
  if tag==None:
    tag        = oldjobcfg['tag']
  if not filenevts:
    checkexpevts==False
  elif checkexpevts==None:
    checkexpevts = 'skim' not in channel.lower() # default for pico analysis jobs
  evtsplit     = any(any(evtsplitexp.match(f) for f in chunkdict[i]) for i in chunkdict)
  noldchunks   = len(chunkdict) # = number of jobs
  goodchunks   = [ ] # good job output
  pendchunks   = [ ] # pending or running jobs
  badchunks    = [ ] # corrupted job output
  misschunks   = [ ] # missing job output
  resubfiles   = [ ] # files to resubmit (if bad or missing)
  
  # NUMBER OF EVENTS
  nprocevents = 0   # total number of processed events
  ndasevents  = oldjobcfg['nevents'] # total number of available events
  if checkdas: #and ndasevents==0: # get nevents straight from DAS
    ndasevents = sample.getnevents(das=True)
    oldjobcfg['nevents'] = ndasevents
  if verbosity>=2:
    print ">>> %-12s = %s"%('ndasevents',ndasevents)
  if verbosity>=3:
    print ">>> %-12s = %s"%('chunkdict',chunkdict)
  
  # CHECK PENDING JOBS
  if checkqueue<0 or pendjobs:
    batch = getbatch(CONFIG,verb=verbosity)
    if checkqueue!=1 or not pendjobs:
      pendjobs = batch.jobs(jobids,verb=verbosity-1) # refresh job list
    else:
      pendjobs = [j for j in pendjobs if j.jobid in jobids] # get new job list with right job id
  
  ###########################################################################
  # CHECK SKIMMED OUTPUT: nanoAOD format, one or more output files per job
  if 'skim' in channel.lower(): # and nfilesperjob>1:
    flagexp   = re.compile(r"-i (.+\.root)") #r"-i ((?:(?<! -).)+\.root[, ])"
    flagexp2  = re.compile(r"--firstevt (\d+) -m (\d+)")
    chunkexp  = re.compile(r"(.+)%s(?:_(\d+))?\.root"%(postfix))
    fpatterns = ["*%s.root"%(postfix)]
    if evtsplit:
      fpatterns.append("*%s_[0-9]*.root"%(postfix))
    if verbosity>=2:
      print ">>> %-12s = %r"%('flagexp',flagexp.pattern)
      print ">>> %-12s = %r"%('flagexp2',flagexp2.pattern)
      print ">>> %-12s = %r"%('fpatterns',fpatterns)
      print ">>> %-12s = %r"%('chunkexp',chunkexp.pattern)
      print ">>> %-12s = %s"%('checkqueue',checkqueue)
      print ">>> %-12s = %s"%('pendjobs',pendjobs)
      print ">>> %-12s = %s"%('jobids',jobids)
    
    # CHECK PENDING JOBS
    pendfiles = [ ]
    for job in pendjobs:
      if verbosity>=3:
        print ">>> Found job %r, status=%r, args=%r"%(job,job.getstatus(),job.args.rstrip())
      if job.getstatus() in ['q','r']:
        if 'HTCondor' in CONFIG.batch:
          jobarg   = str(job.args)
          matches  = flagexp.findall(jobarg)
          matches2 = flagexp2.findall(jobarg)
        else:
          jobarg   = getline(joblist,job.taskid-1)
          matches  = flagexp.findall(jobarg)
          matches2 = flagexp2.findall(jobarg)
        if verbosity>=3:
          print ">>>   jobarg   =",jobarg.replace('\n','')
          print ">>>   matches  =",matches
          print ">>>   matches2 =",matches2
        if not matches:
          continue
        infiles = [ ]
        for file in matches[0].split():
          if not file.endswith('.root'):
            break
          if matches2:
            file += ":%s"%(matches2[0][0]) #,matches2[0][1])
          infiles.append(file)
        LOG.insist(infiles,"Did not find any ROOT files in job arguments %r, matches=%r"%(jobarg,matches))
        ichunk = -1
        for i in chunkdict:
          if all(any(f in c for c in chunkdict[i]) for f in infiles):
            ichunk = i
            break
        LOG.insist(ichunk>=0,
                   "Did not find to which the input files of jobids %s belong! "%(jobids)+
                   "\nichunk=%s,\ninfiles=%s,\nchunkdict=%s"%(ichunk,infiles,chunkdict))
        LOG.insist(len(chunkdict[i])==len(infiles),
                   "Mismatch between input files of jobids %s and chunkdict! "%(jobids)+
                   "\nichunk=%s,\ninfiles=%s,\nchunkdict[%s]=%s"%(ichunk,infiles,ichunk,chunkdict[ichunk]))
        pendchunks.append(ichunk)
    
    # CHECK OUTPUT FILES
    badfiles  = [ ]
    goodfiles = [ ]
    outfiles  = storage.getfiles(filter=fpatterns,verb=verbosity-1) # get output files
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('outfiles',outfiles)
    for fname in outfiles:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      basename = os.path.basename(fname)
      infile   = chunkexp.sub(r"\1.root",basename) # reconstruct input file without path or postfix
      outmatch = chunkexp.match(basename)
      ipart    = int(outmatch.group(2) or -1) if outmatch else -1 # >0 if input file split by events
      nevents  = isvalid(fname) if checkevts else 0 # get number of events processed & check for corruption
      ichunk   = -1
      for i in chunkdict:
        if ichunk>-1: # found corresponding input file
          break
        for chunkfile in chunkdict[i]: # find chunk output file belongs to
          if infile not in chunkfile: continue
          nevtsexp = -1
          inmatch = evtsplitexp.match(chunkfile) # filename:firstevt:maxevts
          if inmatch: # chunk was split by events
            firstevt = int(inmatch.group(2))
            maxevts  = int(inmatch.group(3))
            if firstevt/nevtsexp!=ipart: continue # right file, wrong chunk
            if checkexpevts or verbosity>=2:
              filentot = filenevts.get(inmatch.group(1),-1)
              if filentot>-1 and firstevt>=filentot: # sanity check
                LOG.warning("checkchunks: chunk %d has firstevt=%s>=%s=filentot, which indicates a bug or changed input file %s."%(
                  ichunk,firstevt,filentot,chunkfile))
              nevtsexp = min(maxevts,filentot-firstevt) if filentot>-1 else maxevts # = maxevts; roughly expected nevts (some loss due to cuts)
          elif checkexpevts or verbosity>=2:
            nevtsexp = filenevts.get(chunkfile,-1) # expected number of processed events
          ichunk  = i
          if ichunk in pendchunks:
            if verbosity>=2:
              print ">>>   => Pending..."
            continue
          if nevents<0:
            if verbosity>=2:
              print ">>>   => Bad nevents=%s..."%(nevents)
            badfiles.append(chunkfile)
          else:
            if checkexpevts and nevtsexp>-1 and nevents!=nevtsexp:
              LOG.warning("checkchunks: Found %s processed events, but expected %s for %s..."%(nevents,nevtsexp,fname))
            if verbosity>=2:
              if nevtsexp>-1:
                frac = "%.1f%%"%(100.0*nevents/nevtsexp) if nevtsexp!=0 else ""
                print ">>>   => Good, nevents=%s/%s %s"%(nevents,nevtsexp,frac)
              else:
                print ">>>   => Good, nevents=%s"%(nevents)
            nprocevents += nevents
            goodfiles.append(chunkfile)
      if verbosity>=2:
        if ichunk<0:
          print ">>>   => No match with input file..."
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
    
    # GET FILES for RESUBMISSION + sanity checks
    for ichunk in chunkdict.keys(): # chuckdict length might be changed (popped)
      if ichunk in pendchunks: # output still pending
        continue
      chunkfiles = chunkdict[ichunk]
      keepfiles  = [ ] # do not redo good files in this chunk
      bad        = False # count each chunk only once: bad, else missing
      for fname in chunkfiles: # check bad (corrupted) or missing
        LOG.insist(fname not in resubfiles,"Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                           "Possible overcounting or conflicting job output file format!")
        if fname in goodfiles: # good file, do not resubmit
          keepfiles.append(fname)
        else:
          bad = bad or fname in badfiles # bad (corrupted) or missing, resubmit
          resubfiles.append(fname)
      if len(keepfiles)==len(chunkfiles): # all files in this chunk were succesful
        goodchunks.append(ichunk)
      else:
        if len(keepfiles)==0: # all files bad or missing
          chunkdict.pop(ichunk) # remove chunk from chunkdict to allow for reshuffling
        else: # part of file list bad or missing
          chunkdict[ichunk] = keepfiles # keep record of good ones for bookkeeping, resubmit bad ones
        if bad:
          badchunks.append(ichunk)
        else:
          misschunks.append(ichunk)
  
  
  ###########################################################################
  # CHECK ANALYSIS OUTPUT: custom tree format, one output file per job, numbered post-fix
  else:
    flagexp    = re.compile(r"-t \w*_(\d+)")
    fpattern   = "*%s_[0-9]*.root"%(postfix) # _$postfix_$chunk
    chunkexp   = re.compile(r".+%s_(\d+)\.root"%(postfix))
    if verbosity>=2:
      print ">>> %-12s = %r"%('flagexp',flagexp.pattern)
      print ">>> %-12s = %r"%('fpattern',fpattern)
      print ">>> %-12s = %r"%('chunkexp',chunkexp.pattern)
      print ">>> %-12s = %s"%('checkqueue',checkqueue)
      print ">>> %-12s = %s"%('pendjobs',pendjobs)
      print ">>> %-12s = %s"%('jobids',jobids)
    
    # CHECK PENDING JOBS
    for job in pendjobs:
      if verbosity>=3:
        print ">>> Found job %r, status=%r, args=%r"%(job,job.getstatus(),job.args.rstrip())
      if job.getstatus() in ['q','r']:
        if 'HTCondor' in CONFIG.batch:
          jobarg  = str(job.args)
          matches = flagexp.findall(jobarg)
        else:
          jobarg  = getline(joblist,job.taskid-1)
          matches = flagexp.findall(jobarg)
        if verbosity>=3:
          print ">>> jobarg = %r"%(jobarg)
          print ">>> matches = %s"%(matches)
        if not matches:
          continue
        ichunk = int(matches[0])
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for job %s.%s! "%(ichunk,job.jobid,job.taskid)+
                                       "Possible overcounting!")
        pendchunks.append(ichunk)
    
    # CHECK OUTPUT FILES
    outfiles = storage.getfiles(filter=fpattern,verb=verbosity-1) # get output files
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('outfiles',outfiles)
    for fname in outfiles:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      match = chunkexp.search(fname)
      if match:
        ichunk = int(match.group(1))
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for file %s! "%(ichunk,fname)+
                                       "Possible overcounting or conflicting job output file format!")
        if ichunk in pendchunks:
          continue
      else:
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      nevents = isvalid(fname) if checkevts else 0 # get number of processed events & check for corruption
      if nevents<0:
        if verbosity>=2:
          print ">>>   => Bad, nevents=%s"%(nevents)
        badchunks.append(ichunk)
        # TODO: remove file from outdir to avoid conflicting output ?
      else:
        nevtsexp = 0 # expected number of processed events
        if checkexpevts or verbosity>=2:
          for chunkfile in chunkdict[ichunk]:
            inmatch = evtsplitexp.match(chunkfile) # look for filename:firstevt:maxevts
            if inmatch: # chunk was split by events
              firstevt  = int(inmatch.group(2))
              maxevts   = int(inmatch.group(3))
              filentot  = filenevts.get(inmatch.group(1),-1)
              if firstevt>=filentot: # sanity check
                LOG.warning("checkchunks: chunk %d has firstevt=%s>=%s=filentot, which indicates a bug or changed input file %s."%(
                  ichunk,firstevt,filentot,chunkfile))
              nevtsexp += min(maxevts,filentot-firstevt) if filentot>-1 else maxevts
            else:
              nevtsexp += filenevts.get(chunkfile,-1)
          if checkexpevts and nevtsexp>0 and nevents!=nevtsexp:
            LOG.warning("checkchunks: Found %s processed events, but expected %s for %s..."%(nevents,nevtsexp,fname))
        if verbosity>=2:
          if nevtsexp>-1:
            frac = "%.1f%%"%(100.0*nevents/nevtsexp) if nevtsexp!=0 else ""
            print ">>>   => Good, nevents=%s/%s %s"%(nevents,nevtsexp,frac)
          else:
            print ">>>   => Good, nevents=%s"%(nevents)
        nprocevents += nevents
        goodchunks.append(ichunk)
    
    # GET FILES for RESUBMISSION + sanity checks
    if verbosity>=2:
      print ">>> %-12s = %s"%('nprocevents',nprocevents)
    for ichunk in chunkdict.keys():
      count = goodchunks.count(ichunk)+pendchunks.count(ichunk)+badchunks.count(ichunk)
      LOG.insist(count in [0,1],"Found %d times chunk '%d' (good=%d, pending=%d, bad=%d). "%(
                                count,ichunk,goodchunks.count(ichunk),pendchunks.count(ichunk),badchunks.count(ichunk))+
                                "Possible overcounting or conflicting job output file format!")
      if count==0: # missing chunk
        misschunks.append(ichunk)
      elif ichunk not in badchunks: # good or pending chunk
        continue
      fchunk = chunkdict[ichunk]
      for fname in fchunk:
        LOG.insist(fname not in resubfiles,"Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                           "Possible overcounting or conflicting job output file format!")
      resubfiles.extend(chunkdict[ichunk])
      chunkdict.pop(ichunk) # only save good chunks
  
  ###########################################################################
  
  # PRINT CHUNKS
  goodchunks.sort()
  pendchunks.sort()
  badchunks.sort()
  misschunks.sort()
  def printchunks(jobden,label,text,col,show=False):
   if jobden:
     ratio = color("%4d/%d"%(len(jobden),noldchunks),col,bold=False)
     label = color(label,col,bold=True)
     if not show: # do not print chunks
       jstr = ""
     elif len(jobden)==noldchunks:# do not bother printing out full chunks list
       jobden.sort()
       jstr = ": all %s-%s"%(jobden[0],jobden[-1])
     else: # list pending/failed/missing chunks
       jstr = (": "+', '.join(str(j) for j in jobden))
     print ">>> %s %s - %s%s"%(ratio,label,text,jstr)
   #else:
   #  print ">>> %2d/%d %s - %s"%(len(jobden),len(jobs),label,text)
  rtext = ""
  if ndasevents>0: # report number of processed events
    if checkevts:
      ratio = 100.0*nprocevents/ndasevents
      rcol  = 'green' if ratio>90. else 'yellow' if ratio>80. else 'red'
      rtext = ": "+color("%d/%d (%d%%)"%(nprocevents,ndasevents,ratio),rcol,bold=True)
    else:
      rtext = ": expect %d events"%(ndasevents)
  printchunks(goodchunks,'SUCCESS', "Chunks with output in outdir"+rtext,'green')
  printchunks(pendchunks,'PEND',"Chunks with pending or running jobs",'white',True)
  printchunks(badchunks, 'FAIL', "Chunks with corrupted output in outdir",'red',True)
  printchunks(misschunks,'MISS',"Chunks with no output in outdir",'red',True)
  
  # PRINT LOG FILES for debugging
  if showlogs!=0 and (badchunks or misschunks):
    logglob  = os.path.join(logdir,"*.*.*") #.log
    lognames = sorted(glob.glob(logglob),key=alphanum_key,reverse=True)
    chunkset = {j:None for j in jobids}
    chunkset[jobids[-1]] = oldjobcfg['chunks'] # current job ID
    maxlogs  = showlogs if showlogs>0 else len(badchunks)+len(misschunks)
    for chunk in sorted(badchunks+misschunks)[:maxlogs]:
      for i, jobid in enumerate(reversed(jobids)):
        chunks = chunkset[jobid]
        if chunks==None:
          oldtag  = "_try%d.json"%(oldjobcfg['try'])
          newtag  = "_try%d.json"%(oldjobcfg['try']-i)
          logname = oldcfgname.replace(oldtag,newtag)
          if not os.path.isfile(logname):
            LOG.warning("Did not find job config %r!"%(logname))
            continue
          with open(logname,'r') as file:
            jobcfg = json.load(file)
            chunks = jobcfg.get('chunks',[ ])
            chunkset[jobid] = chunks
        if chunks and chunk in chunks:
          taskid  = chunks.index(chunk)+1
          logexp  = "%d.%d.log"%(jobid,taskid)
          #logexp  = re.compile(".*\.\d{3,}\.%d(?:\.log)?$"%(taskid)) #$JOBNAME.$JOBID.$TASKID.log
          matches = [f for f in lognames if f.endswith(logexp)]
          if matches:
            print ">>>   %s"%(matches[0])
            lognames.remove(matches[0])
            break
      else:
        LOG.warning("Did not find log file for chunk %d"%(chunk))
  
  return resubfiles, chunkdict, len(pendchunks)
  


##################
#   (RE)SUBMIT   #
##################

def main_submit(args):
  """Submit or resubmit jobs to the batch system."""
  if args.verbosity>=1:
    print ">>> main_submit", args
  
  verbosity = args.verbosity
  resubmit  = args.subcommand=='resubmit'
  force     = args.force
  dryrun    = args.dryrun    # prepare job and submit command, but do not submit
  testrun   = args.testrun   # only run a few test jobs
  queue     = args.queue     # queue option for the batch system (job flavor for HTCondor)
  time      = args.time      # maximum time for the batch system
  batchopts = args.batchopts # extra options for the batch system
  batch     = getbatch(CONFIG,verb=verbosity+1)
  
  for jobcfg in preparejobs(args):
    jobid   = None
    cfgname = jobcfg['cfgname']
    jobdir  = jobcfg['jobdir']
    logdir  = jobcfg['logdir']
    outdir  = jobcfg['outdir']
    joblist = jobcfg['joblist'] # text file with list of tasks to be executed per job
    jobname = jobcfg['jobname']
    nchunks = jobcfg['nchunks']
    queue   = jobcfg['queue']
    jkwargs = { # key-word arguments for batch.submit
      'name': jobname, 'opt': batchopts, 'dry': dryrun,
      'short': (testrun>0), 'queue':queue, 'time':time
    }
    if nchunks<=0:
      print ">>>   Nothing to %ssubmit!"%('re' if resubmit else '')
      continue
    if batch.system=='HTCondor':
      # use specific settings for KIT condor
      if 'etp' in GLOB._host:
        script = "python/batch/submit_HTCondor_KIT.sub"
      else:
        script = "python/batch/submit_HTCondor.sub"
      appcmds = ["initialdir=%s"%(jobdir),
                 "mylogfile='log/%s.$(ClusterId).$(ProcId).log'"%(jobname)]
      jkwargs.update({ 'app': appcmds })
    elif batch.system=='SLURM':
      script  = "python/batch/submit_SLURM.sh"
      logfile = os.path.join(logdir,"%x.%A.%a.log") # $JOBNAME.o$JOBID.$TASKID.log
      jkwargs.update({ 'log': logfile, 'array': nchunks })
    #elif batch.system=='SGE':
    #elif batch.system=='CRAB':
    else:
      LOG.throw(NotImplementedError,"Submission for batch system '%s' has not been implemented (yet)..."%(batch.system))
    
    # SUBMIT
    if args.prompt: # ask user confirmation before submitting
      while True:
        submit = raw_input(">>> Do you want to submit %d jobs to the batch system? [y/n] "%(nchunks))
        if any(s in submit.lower() for s in ['q','exit']): # quit this script
          print ">>> Quitting..."
          exit(0)
        elif any(s in submit.lower() for s in ['f','all']):
          print ">>> Force submission..."
          submit = 'y'
          args.prompt = False # stop asking for next samples
        if 'y' in submit.lower(): # submit this job
          jobid = batch.submit(script,joblist,**jkwargs)
          break
        elif 'n' in submit.lower(): # do not submit this job
          print ">>> Not submitting."
          break
        else:
          print ">>> '%s' is not a valid answer, please choose y/n."%submit
    else:
      jobid = batch.submit(script,joblist,**jkwargs)
    
    # WRITE JOBCONFIG
    if jobid!=None:
      jobcfg['jobids'].append(jobid)
      if verbosity>=1:
        print ">>> Creating config file '%s'..."%(cfgname)
      with open(cfgname,'w') as file:
        json.dump(jobcfg,file,indent=2)
  


############################
#   STATUS, HADD & CLEAN   #
############################

def main_status(args):
  """Check status of jobs (succesful/pending/failed/missing), or hadd job output."""
  if args.verbosity>=1:
    print ">>> main_status", args
  
  # SETTING
  eras           = args.eras
  channels       = args.channels
  tag            = args.tag
  checkdas       = args.checkdas     # check number of events from DAS
  checkqueue     = args.checkqueue   # check queue of batch system for pending jobs
  checkevts      = args.checkevts    # validate output file & count events (slow, default)
  checkexpevts   = args.checkexpevts # compare actual to expected number of processed events
  dtypes         = args.dtypes
  filters        = args.samples
  vetoes         = args.vetoes
  force          = args.force
  subcmd         = args.subcommand
  cleanup        = subcmd=='clean' or (subcmd=='hadd' and args.cleanup)
  maxopenfiles   = args.maxopenfiles if subcmd=='hadd' else 0 # maximum number of files opened during hadd, via -n option
  dryrun         = args.dryrun
  verbosity      = args.verbosity
  cmdverb        = max(1,verbosity)
  outdirformat   = CONFIG.outdir
  jobdirformat   = CONFIG.jobdir
  storedirformat = CONFIG.picodir
  jobs           = [ ]
  if subcmd not in ['hadd','clean']:
    if not channels:
      channels = ['*']
    if not eras:
      eras     = ['*']
  
  # LOOP over ERAS
  for era in eras:
    
    # LOOP over CHANNELS
    for channel in channels:
      LOG.header("%s, %s"%(era,channel))
      
      # GET SAMPLES
      jobdir_ = repkey(jobdirformat,ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag)
      jobcfgs = repkey(os.path.join(jobdir_,"config/jobconfig_$CHANNEL$TAG_try[0-9]*.json"),
                       ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag)
      if verbosity>=1:
        print ">>> %-12s = %s"%('cwd',os.getcwd())
        print ">>> %-12s = %s"%('jobdir',jobdir_)
        print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %s"%('dtypes',dtypes)
      samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      if subcmd=='hadd' and 'skim' in channel.lower():
        LOG.warning("Hadding into one file not available for skimming...")
        print
        continue
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if channel!='*' and sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # CHECK JOBS ONLY ONCE
        if checkqueue==1 and not jobs:
          batch = getbatch(CONFIG,verb=verbosity)
          jobs  = batch.jobs(verb=verbosity-1)
        
        # HADD or CLEAN
        if subcmd in ['hadd','clean']:
          cfgname  = sample.jobcfg['config'] # config file
          jobdir   = sample.jobcfg['jobdir'] # job directory
          cfgdir   = sample.jobcfg['cfgdir'] # job configuration directory
          logdir   = sample.jobcfg['logdir'] # job log directory
          outdir   = sample.jobcfg['outdir'] # job output directory
          postfix  = sample.jobcfg['postfix']
          storedir = repkey(storedirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                           DAS=sample.paths[0].strip('/'),GROUP=sample.group)
          storage  = getstorage(storedir,ensure=True,verb=verbosity)
          outfile  = '%s_%s%s.root'%(sample.name,channel,tag)
          infiles  = os.path.join(outdir,'*%s_[0-9]*.root'%(postfix))
          cfgfiles = os.path.join(cfgdir,'job*%s_try[0-9]*.*'%(postfix))
          logfiles = os.path.join(logdir,'*%s*.*.log'%(postfix))
          if verbosity>=1:
            print ">>> %sing job output for '%s'"%(subcmd.capitalize(),sample.name)
            print ">>> %-12s = %r"%('cfgname',cfgname)
            print ">>> %-12s = %r"%('jobdir',jobdir)
            print ">>> %-12s = %r"%('cfgdir',cfgdir)
            print ">>> %-12s = %r"%('outdir',outdir)
            print ">>> %-12s = %r"%('storedir',storedir)
            print ">>> %-12s = %s"%('infiles',infiles)
            if subcmd=='hadd':
              print ">>> %-12s = %r"%('outfile',outfile)
          resubfiles, chunkdict, npend = checkchunks(sample,channel=channel,tag=tag,jobs=jobs,checkqueue=checkqueue,
                                                     checkevts=checkevts,das=checkdas,checkexpevts=checkexpevts,verb=verbosity)
          if (len(resubfiles)>0 or npend>0) and not force: # only clean or hadd if all jobs were successful
            LOG.warning("Cannot %s job output because %d chunks need to be resubmitted..."%(subcmd,len(resubfiles))+
                        " Please use -f or --force to %s anyway.\n"%(subcmd))
            continue
          
          if subcmd=='hadd':
            #haddcmd = 'hadd -f %s %s'%(outfile,infiles)
            #haddout = execute(haddcmd,dry=dryrun,verb=max(1,verbosity))
            haddout = storage.hadd(infiles,outfile,dry=dryrun,verb=cmdverb,maxopenfiles=maxopenfiles)
            # TODO: add option to print out cutflow for outfile
            #os.system(haddcmd)
          
          # CLEAN UP
          # TODO: check if hadd was succesful with isvalid
          if cleanup:
            allcfgs = os.path.join(cfgdir,"job*_try[0-9]*.*")
            rmcmd   = None
            if len(glob.glob(allcfgs))==len(glob.glob(cfgfiles)): # check for other jobs
              if verbosity>=2:
                print ">>> %-12s = %s"%('cfgfiles',cfgfiles)
              rmcmd = "rm -r %s"%(jobdir) # remove whole job directory
            else: # only remove files related to this job (era/channel/sample)
              rmfiles   = [ ]
              rmfileset = [infiles,cfgfiles,logfiles]
              for files in rmfileset:
                if len(glob.glob(files))>0:
                  rmfiles.append(files)
              if verbosity>=2:
                print ">>> %-12s = %s"%('cfgfiles',cfgfiles)
                print ">>> %-12s = %s"%('rmfileset',rmfileset)
              if rmfiles:
                rmcmd = "rm %s"%(' '.join(rmfiles))
            if rmcmd:
              if verbosity>=1:
                rmcmd = lreplace(rmcmd,'rm',"rm -v",1)
              rmout = execute(rmcmd,dry=dryrun,verb=cmdverb)
        
        # ONLY CHECK STATUS
        else:
          showlogs = args.showlogs # print log files of failed jobs
          cfgname  = sample.jobcfg['config'] # config file
          jobdir   = sample.jobcfg['jobdir']
          outdir   = sample.jobcfg['outdir']
          logdir   = sample.jobcfg['logdir']
          if verbosity>=1:
            print ">>> Checking job status for '%s'"%(sample.name)
            print ">>> %-12s = %r"%('cfgname',cfgname)
            print ">>> %-12s = %r"%('jobdir',jobdir)
            print ">>> %-12s = %r"%('outdir',outdir)
            print ">>> %-12s = %r"%('logdir',logdir)
          checkchunks(sample,channel=channel,tag=tag,jobs=jobs,showlogs=showlogs,
                      checkqueue=checkqueue,checkevts=checkevts,das=checkdas,verb=verbosity)
        
        print
      
      if not found:
        print_no_samples(dtypes,filters,vetoes,jobdir_,jobcfgs)
  


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  description = "Central script to process nanoAOD for skimming or analysis."
  parser = ArgumentParser(prog='pico.py',description=description,epilog="Good luck!")
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0,
                                                help="set verbosity" )
  parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help='skimming or analysis channel to run')
  parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help='year or era to specify the sample list')
  parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ],
                          metavar='PATTERN',    help="filter these samples; glob patterns like '*' and '?' wildcards are allowed" )
  parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ],
                          metavar='PATTERN',    help="exclude/veto these samples; glob patterns are allowed" )
  parser_sam.add_argument('--dtype',            dest='dtypes', choices=GLOB._dtypes, default=GLOB._dtypes, nargs='+',
                                                help='filter these data type(s)')
  parser_sam.add_argument('-D','--das',         dest='checkdas', action='store_true',
                                                help="check DAS for total number of events" )
  parser_sam.add_argument('--dasfiles',         dest='dasfiles', action='store_true',
                                                help="get files from DAS (instead of local storage, if predefined)" )
  parser_sam.add_argument('-t','--tag',         dest='tag', default="",
                                                help='tag for output file name')
  parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
                                                help='force overwrite')
  parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help='dry run: prepare job without submitting for debugging purposes')
  parser_sam.add_argument('-E', '--opts',       dest='extraopts', type=str, nargs='+', default=[ ],
                          metavar='KEY=VALUE',  help="extra options for the skim or analysis module, "
                                                     "passed as list of 'KEY=VALUE', separated by spaces")
  parser_job = ArgumentParser(add_help=False,parents=[parser_sam])
  parser_job.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during job to increase processing speed and ensure stability" )
  parser_job.add_argument('-T','--test',        dest='testrun', type=int, nargs='?', const=10000, default=0,
                          metavar='NEVTS',      help='run a test with limited nummer of jobs and events, default nevts=%(const)d' )
  parser_job.add_argument('--checkqueue',       dest='checkqueue', type=int, nargs='?', const=1, default=-1,
                          metavar='N',          help="check job status: 0 (no check), 1 (check once, fast), -1 (check every job, slow, default)" ) # speed up if batch is slow
  parser_job.add_argument('--skipevts',         dest='checkevts', action='store_false',
                                                help="skip validation and counting of events in output files (faster)" )
  parser_job.add_argument('--checkexpevts',     dest='checkexpevts', action='store_true', default=None,
                                                help="check if the actual number of processed events is the same as the expected number" )
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
  parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
                                                help='extra options for the batch system')
  parser_job.add_argument('-M','--time',        dest='time', default=None,
                                                help='maximum run time of job')
  parser_job.add_argument('-q','--queue',       dest='queue', default=str(CONFIG.queue),
                                                help='queue of batch system (job flavor on HTCondor)')
  parser_job.add_argument('-P','--prompt',      dest='prompt', action='store_true',
                                                help='ask user permission before submitting a sample')
  parser_job.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help='preselection to be shipped to skimjob.py during run command')
  parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=-1,
                                                help='number of files per job, default=%d'%(CONFIG.nfilesperjob))
  parser_job.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=-1,
                          metavar='NEVTS',      help='maximum number of events per job to process (split large files), default=%d"'%(CONFIG.maxevtsperjob))
  parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1,
                          metavar='NFILES',     help="divide default number of files per job, default=%(const)d" )
  parser_job.add_argument('--tmpdir',           dest='tmpdir', type=str, default=None,
                                                help="for skimming only: temporary output directory befor copying to outdir")
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  help_ins = "install"
  help_lst = "list configuration"
  help_get = "get information from configuration or samples"
  help_set = "set given variable in the configuration file"
  help_rmv = "remove given variable from the configuration file"
  help_wrt = "write files to text file"
  help_chl = "link a channel to a module in the configuration file"
  help_era = "link an era to a sample list in the configuration file"
  help_run = "run nanoAOD processor locally"
  help_sub = "submit processing jobs"
  help_res = "resubmit failed processing jobs"
  help_sts = "status of processing jobs"
  help_hdd = "hadd processing job output"
  help_cln = "remove job output"
  parser_ins = subparsers.add_parser('install',  parents=[parser_cmn], help=help_ins, description=help_ins)
  parser_lst = subparsers.add_parser('list',     parents=[parser_cmn], help=help_lst, description=help_lst)
  parser_get = subparsers.add_parser('get',      parents=[parser_sam], help=help_get, description=help_get)
  parser_set = subparsers.add_parser('set',      parents=[parser_cmn], help=help_set, description=help_set)
  parser_rmv = subparsers.add_parser('rm',       parents=[parser_cmn], help=help_rmv, description=help_rmv)
  parser_wrt = subparsers.add_parser('write',    parents=[parser_sam], help=help_wrt, description=help_wrt)
  parser_chl = subparsers.add_parser('channel',  parents=[parser_lnk], help=help_chl, description=help_chl)
  parser_era = subparsers.add_parser('era',      parents=[parser_lnk], help=help_era, description=help_era)
  parser_run = subparsers.add_parser('run',      parents=[parser_sam], help=help_run, description=help_run)
  parser_sub = subparsers.add_parser('submit',   parents=[parser_job], help=help_sub, description=help_sub)
  parser_res = subparsers.add_parser('resubmit', parents=[parser_job], help=help_res, description=help_res)
  parser_sts = subparsers.add_parser('status',   parents=[parser_chk], help=help_sts, description=help_sts)
  parser_hdd = subparsers.add_parser('hadd',     parents=[parser_chk], help=help_hdd, description=help_hdd)
  parser_cln = subparsers.add_parser('clean',    parents=[parser_chk], help=help_cln, description=help_cln)
  #parser_get.add_argument('variable',           help='variable to change in the config file')
  parser_get.add_argument('variable',           help='variable to get information on',choices=['samples','files','nevents','nevts',]+CONFIG.keys())
  parser_set.add_argument('variable',           help='variable to set or change in the config file')
  parser_set.add_argument('key',                help='channel or era key name', nargs='?', default=None)
  parser_set.add_argument('value',              help='value for given value')
  parser_wrt.add_argument('listname',           help='file name of text file for file list, default=%(default)r', nargs='?', default=str(CONFIG.filelistdir))
  parser_rmv.add_argument('variable',           help='variable to remove from the config file')
  parser_rmv.add_argument('key',                help='channel or era key name to remove', nargs='?', default=None)
  parser_chl.add_argument('key',                metavar='channel', help='channel key name')
  parser_chl.add_argument('value',              metavar='module',  help='module linked to by given channel')
  parser_era.add_argument('key',                metavar='era',     help='era key name')
  parser_era.add_argument('value',              metavar='samples', help='samplelist linked to by given era')
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help='type of installation: standalone or compiled in CMSSW')
  parser_get.add_argument('-U','--url',         dest='inclurl', action='store_true',
                                                help="include XRootD url in filename for 'get files'" )
  parser_get.add_argument('-L','--limit',       dest='limit', type=int, default=-1,
                          metavar='NFILES',     help="limit number files in list for 'get files'" )
  parser_get.add_argument('-l','--local',       dest='checklocal', action='store_true',
                                                help="compute total number of events in storage system (not DAS) for 'get files' or 'get nevents'" )
  parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=str(CONFIG.filelistdir), default="",
                          metavar='FILE',       help="write file list, default=%(const)r" )
  parser_get.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)" )
  parser_wrt.add_argument('-n','--nevts',       dest='getnevts', action='store_true',
                                                help="get nevents per file" )
  parser_wrt.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)" )
  parser_wrt.add_argument('-T','--try',         dest='retries', type=int, default=1, action='store',
                                                help="number of retries if file is not found" )
  parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                          metavar='NEVTS',      help='maximum number of events (per file) to process')
  parser_run.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help='preselection to be shipped to skimjob.py during run command')
  parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
                                                help="maximum number of input files to process (per sample), default=%(default)d")
  parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
                                                help="number of samples to run, default=%(default)d")
  parser_run.add_argument('-i', '--input',      dest='infiles', nargs='+', default=[ ],
                                                help="input files (nanoAOD)")
  parser_run.add_argument('-o', '--outdir',     dest='outdir', type=str, default='output',
                                                help="output directory, default=%(default)r")
  parser_run.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during run to increase processing speed and ensure stability" )
  parser_sts.add_argument('-l','--log',         dest='showlogs', type=int, nargs='?', const=-1, default=0,
                          metavar='NLOGS',      help="show log files of failed jobs: 0 (show none), -1 (show all), n (show max n)" )
  #parser_hdd.add_argument('--keep',             dest='cleanup', action='store_false',
  #                                              help="do not remove job output after hadd'ing" )
  parser_hdd.add_argument('-m','--maxopenfiles',dest='maxopenfiles', type=int, default=CONFIG.maxopenfiles,
                          metavar='NFILES',     help="maximum numbers to be opened during hadd, default=%(default)d" )
  parser_hdd.add_argument('-r','--clean',       dest='cleanup', action='store_true',
                                                help="remove job output (to be used after hadd'ing)" )
  
  # SUBCOMMAND ABBREVIATIONS, e.g. 'pico.py s' or 'pico.py sub'
  args = sys.argv[1:]
  if args:
    subcmds = [ # fix order for abbreviations
      'channel','era',
      'run','submit','resubmit','status','hadd','clean',
      'install','list','set','rm','write',
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  
  # SUBCOMMAND MAINs
  os.chdir(CONFIG.basedir)
  if args.subcommand=='install':
    main_install(args)
  if args.subcommand=='list':
    main_list(args)
  elif args.subcommand=='get':
    main_get(args)
  elif args.subcommand=='set':
    main_set(args)
  elif args.subcommand=='write':
    main_write(args)
  elif args.subcommand in ['channel','era']:
    main_link(args)
  elif args.subcommand=='rm':
    main_rm(args)
  elif args.subcommand=='run':
    main_run(args)
  elif args.subcommand in ['submit','resubmit']:
    main_submit(args)
  elif args.subcommand in ['status','hadd','clean']:
    main_status(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  

