#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, sys, re, glob, json
from datetime import datetime
from collections import OrderedDict
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.PicoProducer.tools.file import ensuredir, ensurefile, getline
from TauFW.PicoProducer.tools.utils import execute, chunkify, repkey
from TauFW.PicoProducer.tools.log import Logger, color, bold, header
from TauFW.PicoProducer.analysis.utils import getmodule, ensuremodule
from TauFW.PicoProducer.batch.utils import getbatch, getsamples, getcfgsamples
from TauFW.PicoProducer.storage.utils import getstorage
from argparse import ArgumentParser
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
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
#   GET   #
###########

def main_get(args):
  """Get information of given variable."""
  if args.verbosity>=1:
    print ">>> main_get", args
  variable  = args.variable
  eras      = args.eras
  dtypes    = args.dtypes
  filters   = args.samples
  vetoes    = args.vetoes
  channels  = args.channels or [""]
  checkdas  = args.checkdas
  writedir  = args.write
  tag       = args.tag
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
    print ">>> %-14s = %s"%('variable',variable)
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
    
  # SAMPLES
  if variable=='files':
    
    # LOOP over ERAS & CHANNELS
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        
        # VERBOSE
        if verbosity>=1:
          print ">>> %-12s = %r"%('channel',channel)
        
        # GET SAMPLES
        assert era in CONFIG.eras, "Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras)
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,verb=verbosity)
        
        # LOOP over SAMPLES
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>> %s"%(bold(path))
            infiles = sample.getfiles(url=False,verb=verbosity+1)
            if checkdas:
              ndasevents = sample.getnevents(verb=verbosity+1)
              print ">>> %-12s = %s"%('ndasevents',ndasevents)
            print ">>> %-12s = %r"%('url',sample.url)
            print ">>> %-12s = %s"%('nfiles',len(infiles))
            print ">>> %-12s = [ "%('infiles')
            for file in infiles:
              print ">>>   %r"%file
            print ">>> ]"
            if writedir:
              flistname = repkey(writedir,ERA=era,GROUP=sample.group,SAMPLE=sample.name,TAG=tag)
              print ">>> Write list to %r..."%(flistname)
              ensuredir(os.path.dirname(flistname))
              with open(flistname,'w+') as flist:
                for infile in infiles:
                  flist.write(infile+'\n')
  
  # CONFIGURATION
  else:
    if variable in CONFIG:
      print ">>> Configuration of %r: %s"%(variable,color(CONFIG[variable]))
    else:
      print ">>> Did not find %r in the configuration"%(variable)
  


###########
#   SET   #
###########

def main_set(args):
  """Set variables in the config file."""
  if args.verbosity>=1:
    print ">>> main_set", args
  variable  = args.variable
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print '-'*80
  print ">>> Setting variable '%s' to '%s' config"%(variable,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if variable=='all':
    if 'default' in value:
      GLOB.setdefaultconfig(verb=verb)
    else:
      LOG.warning("Did not recognize value '%s'. Did you mean 'default'?"%(value))
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
  print ">>> Linking %s '%s' to '%s' in config"%(variable,key,value)
  if verbosity>=1:
    print ">>> %-14s = %s"%('cfgname',cfgname)
    print ">>> %-14s = %s"%('config',CONFIG)
    print '-'*80
  if '_' in value:
    LOG.throw(IOError,"Value given for %s (%s) cannot contain '_'!"%(variable,value))
  if varkey not in CONFIG:
    CONFIG[varkey] = { }
  assert isinstance(CONFIG[varkey],dict), "%s in %s has to be a dictionary"%(varkey,cfgname)
  CONFIG[varkey][key] = value
  CONFIG.write()
  


###########
#   RUN   #
###########

def main_run(args):
  """Run given module locally."""
  if args.verbosity>=1:
    print ">>> main_run", args
  eras      = args.eras
  channels  = args.channels
  tag       = args.tag
  dtypes    = args.dtypes
  filters   = args.samples
  vetoes    = args.vetoes
  force     = args.force
  maxevts   = args.maxevts
  nfiles    = args.nfiles
  nsamples  = args.nsamples
  dryrun    = args.dryrun
  verbosity = args.verbosity
  
  # LOOP over ERAS
  for era in eras:
    moddict = { } # save time by loading samples and get their files only once
    
    # LOOP over CHANNELS
    for channel in channels:
      print header("%s, %s"%(era,channel))
      
      # CHANNEL -> MODULE
      assert channel in CONFIG.channels, "Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels)
      module = CONFIG.channels[channel]
      if channel!='test' and 'skim' not in module:
        ensuremodule(module)
      outdir = ensuredir('output')
      
      # PROCESSOR
      if 'skim' in channel:
        processor = "skimjob.py"
      elif channel=='test':
        processor = "test.py"
      else:
        processor = "picojob.py"
      processor   = os.path.join("python/processors",processor)
      if not os.path.isfile(processor):
        LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
      #processor = os.path.abspath(procpath)
      
      # VERBOSE
      if verbosity>=1:
        print '-'*80
        print ">>> Running %r"%(channel)
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %r"%('processor',processor)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
        print ">>> %-12s = %r"%('outdir',outdir)
      
      # GET SAMPLES
      if filters or vetoes or dtypes:
        assert era in CONFIG.eras, "Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras)
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,moddict=moddict,verb=verbosity)
        if nsamples>0:
          samples = samples[:nsamples]
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
        filetag = tag
        if sample:
          filetag += '_'+sample.name
        if verbosity>=1:
          print ">>> %-12s = %s"%('sample',sample)
          print ">>> %-12s = %r"%('filetag',filetag)
        
        # GET FILES
        infiles = 0
        if sample:
          nevents = 0
          infiles = sample.getfiles(verb=verbosity)
          if nfiles>0:
            infiles = infiles[:nfiles]
          if verbosity==1:
            print ">>> %-12s = %s"%('nfiles',len(infiles))
            print ">>> %-12s = [ "%('infiles')
            for file in infiles:
              print ">>>   %r"%file
            print ">>> ]"
        if verbosity==1:
          print '-'*80
        
        # RUN
        runcmd = processor
        if 'skim' in channel:
          runcmd += " -y %s -o %s --jec-sys"%(era,outdir)
        elif 'test' in channel:
          runcmd += " -o %s"%(outdir)
        else: # analysis
          runcmd += " -y %s -c %s -M %s -o %s"%(era,channel,module,outdir)
        if filetag:
          runcmd += " -t %s"%(filetag)
        if maxevts:
          runcmd += " -m %s"%(maxevts)
        if infiles:
          runcmd += " -i %s"%(' '.join(infiles))
        #elif nfiles:
        #  runcmd += " --nfiles %s"%(nfiles)
        print "Executing: "+bold(runcmd)
        if not dryrun:
          #execute(runcmd,dry=dryrun,verb=verbosity+1) # real-time print out does not work well with python script 
          os.system(runcmd)
      


####################
#   PREPARE JOBS   #
####################

def preparejobs(args):
  """Help function to iterate over samples per given channel and era and prepare job config and list."""
  if args.verbosity>=1:
    print ">>> preparejobs", args
  
  resubmit     = args.subcommand=='resubmit'
  eras         = args.eras
  channels     = args.channels
  tag          = args.tag
  dtypes       = args.dtypes
  filters      = args.samples
  vetoes       = args.vetoes
  checkdas     = args.checkdas
  checkqueue   = args.checkqueue
  prefetch     = args.prefetch
  nfilesperjob = args.nfilesperjob
  split_nfpj   = args.split_nfpj
  verbosity    = args.verbosity
  jobs         = [ ]
  
  # LOOP over ERAS
  for era in eras:
    moddict = { } # save time by loading samples and get their file list only once
    
    # LOOP over CHANNELS
    for channel in channels:
      print header("%s, %s"%(era,channel))
      
      # CHANNEL -> MODULE
      assert channel in CONFIG.channels, "Channel '%s' not found in the configuration file. Available: %s"%(channel,CONFIG.channels)
      module = CONFIG.channels[channel]
      if channel!='test' and 'skim' not in channel:
        ensuremodule(module)
      if verbosity>=1:
        print '-'*80
        print ">>> %-12s = %r"%('channel',channel)
        print ">>> %-12s = %r"%('module',module)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %r"%('dtypes',dtypes)
      
      # PROCESSOR
      if 'skim' in channel:
        processor = module
      elif channel=='test':
        processor = module
      else:
        processor = "picojob.py"
      procpath  = os.path.join("python/processors",processor)
      if not os.path.isfile(procpath):
        LOG.throw(IOError,"Processor '%s' does not exist in '%s'..."%(processor,procpath))
      processor = os.path.abspath(procpath)
      if verbosity>=1:
        print ">>> %-12s = %r"%('processor',processor)
        print '-'*80
      
      # GET SAMPLES
      jobdirformat = CONFIG.jobdir # for job config & log files
      outdirformat = CONFIG.nanodir if 'skim' in channel else CONFIG.outdir # for job output
      if resubmit:
        # TODO: allow user to resubmit given config file
        jobcfgs  = repkey(os.path.join(jobdirformat,"config/jobconfig_$SAMPLE$TAG_try[0-9]*.json"),
                          ERA=era,SAMPLE='*',CHANNEL=channel,TAG=tag)
        if verbosity>=2:
          print ">>> %-12s = %s"%('cwd',os.getcwd())
          print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      else:
        assert era in CONFIG.eras, "Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras)
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,moddict=moddict,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # DIRECTORIES
        subtry        = sample.subtry+1 if resubmit else 1
        jobids        = sample.jobcfg.get('jobids',[ ])
        postfix       = "_%s%s"%(channel,tag)
        jobtag        = '_%s%s_try%d'%(channel,tag,subtry)
        jobname       = sample.name+jobtag.rstrip('try1').rstrip('_')
        nfilesperjob_ = sample.nfilesperjob if sample.nfilesperjob>0 else nfilesperjob
        if split_nfpj>1:
          nfilesperjob_ = min(1,nfilesperjob_/split_nfpj)
        outdir        = repkey(outdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                            DAS=sample.paths[0].strip('/'),GROUP=sample.group)
        jobdir        = ensuredir(repkey(jobdirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                                      DAS=sample.paths[0].strip('/'),GROUP=sample.group))
        cfgdir        = ensuredir(jobdir,"config")
        logdir        = ensuredir(jobdir,"log")
        cfgname       = "%s/jobconfig%s.json"%(cfgdir,jobtag)
        joblist       = '%s/jobarglist%s.txt'%(cfgdir,jobtag)
        if verbosity==1:
          print ">>> %-12s = %s"%('cfgname',cfgname)
          print ">>> %-12s = %s"%('joblist',joblist)
        elif verbosity>=2:
          print '-'*80
          print ">>> Preparing job %ssubmission for '%s'"%("re" if resubmit else "",sample.name)
          print ">>> %-12s = %r"%('processor',processor)
          print ">>> %-12s = %r"%('jobname',jobname)
          print ">>> %-12s = %r"%('jobtag',jobtag)
          print ">>> %-12s = %r"%('postfix',postfix)
          print ">>> %-12s = %r"%('outdir',outdir)
          print ">>> %-12s = %r"%('cfgdir',cfgdir)
          print ">>> %-12s = %r"%('logdir',logdir)
          print ">>> %-12s = %r"%('cfgname',cfgname)
          print ">>> %-12s = %r"%('joblist',joblist)
          print ">>> %-12s = %s"%('try',subtry)
          print ">>> %-12s = %r"%('jobids',jobids)
        
        # CHECKS
        if os.path.isfile(cfgname):
          # TODO: check for running jobs
          LOG.warning("Job configuration '%s' already exists and will be overwritten! "+
                      "Beware of conflicting job output!"%(cfgname))
        if not resubmit:
          cfgpattern = re.sub(r"(?<=try)\d+(?=.json$)",r"*",cfgname)
          cfgnames   = [f for f in glob.glob(cfgpattern) if not f.endswith("_try1.json")]
          if cfgnames:
            LOG.warning("Job configurations for resubmission already exists! This can cause conflicting job output!"+
              "If you are sure you want to submit from scratch, please remove these files:\n>>>   "+"\n>>>   ".join(cfgnames))
        storage = getstorage(outdir,verb=verbosity,ensure=True)
        
        # GET FILES
        nevents = 0
        if resubmit: # resubmission
          if checkqueue==0 and not jobs: # check jobs only once
            batch = getbatch(CONFIG,verb=verbosity)
            jobs  = batch.jobs(verb=verbosity-1)
          infiles, chunkdict = checkchuncks(sample,outdir=outdir,channel=channel,tag=tag,jobs=jobs,
                                         checkqueue=checkqueue,das=checkdas,verb=verbosity)
          nevents = sample.jobcfg['nevents'] # updated in checkchuncks
        else: # first-time submission
          infiles   = sample.getfiles(verb=verbosity-1)
          if checkdas:
            nevents = sample.getnevents()
          chunkdict = { }
        if args.testrun:
          infiles = infiles[:2]
        if verbosity==1:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
        elif verbosity>=2:
          print ">>> %-12s = %s"%('nfilesperjob',nfilesperjob_)
          print ">>> %-12s = %s"%('nfiles',len(infiles))
          print ">>> %-12s = [ "%('infiles')
          for file in infiles:
            print ">>>   %r"%file
          print ">>> ]"
          print ">>> %-12s = %s"%('nevents',nevents)
        
        # CHUNKS
        infiles.sort() # to have consistent order with resubmission
        chunks    = [ ] # chunk indices
        fchunks   = chunkify(infiles,nfilesperjob_) # file chunks
        nfiles    = len(infiles)
        nchunks   = len(fchunks)
        if verbosity>=1:
          print ">>> %-12s = %s"%('nchunks',nchunks)
        if verbosity>=2:
          print '-'*80
        
        # WRITE JOB LIST with arguments per job
        if args.verbosity>=1:
          print ">>> Creating job list %s..."%(joblist)
        with open(joblist,'w') as listfile:
          ichunk = 0
          for fchunk in fchunks:
            while ichunk in chunkdict:
              ichunk   += 1 # allows for different nfilesperjob on resubmission
              continue
            jobfiles    = ' '.join(fchunk) # list of input files
            filetag     = postfix
            if 'skim' not in channel:
              filetag  += "_%d"%(ichunk)
            jobcmd      = processor
            if 'skim' in channel:
              jobcmd += " -y %s --copydir %s -t %s --jec-sys"%(era,outdir,filetag)
            elif 'test' in channel:
              jobcmd += " -o %s -t %s -i %s"%(outdir,filetag)
            else:
              jobcmd += " -y %s -c %s -M %s --copydir %s -t %s"%(era,channel,module,outdir,filetag)
            if prefetch:
              jobcmd += " -p"
            jobcmd += " -i %s"%(jobfiles) # add last
            if args.verbosity>=1:
              print jobcmd
            listfile.write(jobcmd+'\n')
            chunkdict[ichunk] = fchunk
            chunks.append(ichunk)
        
        # JSON CONFIG
        jobcfg = OrderedDict([
          ('time',str(datetime.now())),
          ('group',sample.group), ('paths',sample.paths), ('name',sample.name), ('nevents',nevents),
          ('channel',channel),    ('module',module),
          ('jobname',jobname),    ('jobtag',jobtag),      ('tag',tag),          ('postfix',postfix),
          ('try',subtry),         ('jobids',jobids),
          ('outdir',outdir),      ('jobdir',jobdir),      ('cfgdir',cfgdir),    ('logdir',logdir),
          ('cfgname',cfgname),    ('joblist',joblist),
          ('nfiles',nfiles),      ('files',infiles),      ('nfilesperjob',nfilesperjob_), #('nchunks',nchunks),
          ('nchunks',nchunks),    ('chunks',chunks),      ('chunkdict',chunkdict),
        ])
        
        # YIELD
        yield jobcfg
        print
        #if args.testrun:
        #  break # only run one sample
      
      if not found:
        print ">>> Did not find any samples."
        if verbosity>=1:
          print ">>> %-8s = %s"%('filters',filters)
          print ">>> %-8s = %s"%('vetoes',vetoes)
    


##################
#   CHECK JOBS   #
##################

def checkchuncks(sample,**kwargs):
  """Help function to check jobs status: success, pending, failed or missing.
  Return list of files to be resubmitted, and a dictionary between chunk index and input files."""
  outdir       = kwargs.get('outdir',      None)
  channel      = kwargs.get('channel',     None)
  tag          = kwargs.get('tag',         None)
  checkqueue   = kwargs.get('checkqueue', False)
  pendjobs     = kwargs.get('jobs',         [ ])
  checkdas     = kwargs.get('das',         True)
  verbosity    = kwargs.get('verb',           0)
  oldjobcfg    = sample.jobcfg
  oldcfgname   = oldjobcfg['config']
  chunkdict    = oldjobcfg['chunkdict'] # filenames
  jobids       = oldjobcfg['jobids']
  joblist      = oldjobcfg['joblist']
  postfix      = oldjobcfg['postfix']
  nfilesperjob = oldjobcfg['nfilesperjob']
  if outdir==None:
    outdir     = oldjobcfg['outdir']
  storage      = getstorage(outdir,ensure=True)
  if channel==None:
    channel    = oldjobcfg['channel']
  if tag==None:
    tag        = oldjobcfg['tag']
  noldchunks   = len(chunkdict) # = number of jobs
  goodchunks   = [ ] # good job output
  pendchunks   = [ ] # pending or running jobs
  badchunks    = [ ] # corrupted job output
  misschunks   = [ ] # missing job output
  resubfiles   = [ ] # files to resubmit (if bad or missing)
  
  # NUMBER OF EVENTS
  nprocevents = 0   # total number of processed events
  ndasevents  = oldjobcfg['nevents'] # total number of available events
  if checkdas and oldjobcfg['nevents']==0:
    ndasevents = sample.getnevents()
    oldjobcfg['nevents'] = ndasevents
  if verbosity>=2:
    print ">>> %-12s = %s"%('ndasevents',ndasevents)
  if verbosity>=3:
    print ">>> %-12s = %s"%('chunkdict',chunkdict)
  
  # CHECK PENDING JOBS
  if checkqueue<0 or pendjobs:
    batch = getbatch(CONFIG,verb=verbosity)
    if checkqueue!=1 or not pendjobs:
      pendjobs = batch.jobs(jobids,verb=verbosity-1) # get refreshed job list
    else:
      pendjobs = [j for j in pendjobs if j.jobid in jobids] # get new job list with right job id
  
  ###########################################################################
  # CHECK SKIMMED OUTPUT: nanoAOD format, one or more output files per job
  if 'skim' in channel: # and nfilesperjob>1:
    flagexp  = re.compile(r"-i (.+\.root)") #r"-i ((?:(?<! -).)+\.root[, ])"
    fpattern = "*%s.root"%(postfix)
    chunkexp = re.compile(r".+%s\.root"%(postfix))
    if verbosity>=2:
      print ">>> %-12s = %r"%('flagexp',flagexp.pattern)
      print ">>> %-12s = %r"%('fpattern',fpattern)
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
        if CONFIG.batch=='HTCondor':
          jobarg  = str(job.args)
          matches = flagexp.findall(jobarg)
        else:
          jobarg  = getline(joblist,job.taskid-1)
          matches = flagexp.findall(jobarg)
        if verbosity>=3:
          print ">>> matches = ",matches
        if not matches:
          continue
        infiles = [ ]
        for file in matches[0].split():
          if not file.endswith('.root'):
            break
          infiles.append(file)
        LOG.insist(infiles,"Did not find any root files in %r, matches=%r"%(jobarg,matches))
        ichunk = -1
        for i in chunkdict:
          if all(f in chunkdict[i] for f in infiles):
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
    fnames    = storage.getfiles(filter=fpattern,verb=verbosity-1)
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('fnames',fnames)
    for fname in fnames:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      infile = os.path.basename(fname.replace(postfix+".root",".root")) # reconstruct input file
      nevents = isvalid(fname) # check for corruption
      ichunk = -1
      fmatch = None
      for i in chunkdict:
        if fmatch:
          break
        for chunkfile in chunkdict[i]:
          if infile in chunkfile: # find chunk input file belongs to
            ichunk = i
            fmatch = chunkfile
            break
      if ichunk<0:
        if verbosity>=2:
          print ">>>   => No match..."
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      if ichunk in pendchunks:
        if verbosity>=2:
          print ">>>   => Pending..."
        continue
      if nevents<0:
        if verbosity>=2:
          print ">>>   => Bad nevents=%s..."%(nevents)
        badfiles.append(fmatch)
      else:
        if verbosity>=2:
          print ">>>   => Good, nevents=%s"%(nevents)
        nprocevents += nevents
        goodfiles.append(fmatch)
    
    # GET FILES for RESUBMISSION + sanity checks
    for ichunk in chunkdict.keys():
      if ichunk in pendchunks:
        continue
      chunkfiles = chunkdict[ichunk]
      if all(f in goodfiles for f in chunkfiles): # all files succesful
        goodchunks.append(ichunk)
        continue
      bad = False # count each chunk only once: bad, else missing
      for fname in chunkfiles:
        LOG.insist(fname not in resubfiles,"Found file for chunk '%d' more than once: %s "%(ichunk,fname)+
                                           "Possible overcounting or conflicting job output file format!")
        if fname in badfiles:
          bad = True
          resubfiles.append(fname)
        elif fname not in goodfiles:
          resubfiles.append(fname)
      if bad:
        badchunks.append(ichunk)
      else:
        misschunks.append(ichunk)
      chunkdict.pop(ichunk)
  
  ###########################################################################
  # CHECK ANALYSIS OUTPUT: custom tree format, one output file per job
  else:
    flagexp  = re.compile(r"-t \w*(\d+)")
    fpattern = "*%s_[0-9]*.root"%(postfix)
    chunkexp = re.compile(r".+%s_(\d+)\.root"%(postfix))
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
        if CONFIG.batch=='HTCondor':
          jobarg  = str(job.args)
          matches = flagexp.findall(jobarg)
        else:
          jobarg  = getline(joblist,job.taskid-1)
          matches = flagexp.findall(jobarg)
        if verbosity>=3:
          print ">>> matches = ",matches
        if not matches:
          continue
        ichunk = int(matches[0])
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for job %s.%s! "%(ichunk,job.jobid,job.taskid)+
                                       "Possible overcounting!")
        pendchunks.append(ichunk)
    
    # CHECK OUTPUT FILES
    fnames = storage.getfiles(filter=fpattern,verb=verbosity-1)
    if verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('fnames',fnames)
    for fname in fnames:
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      match = chunkexp.search(fname)
      if match:
        ichunk = int(match.group(1))
        LOG.insist(ichunk in chunkdict,"Found an impossible chunk %d for file %s!"%(ichunk,fname)+
                                       "Possible overcounting or conflicting job output file format!")
        if ichunk in pendchunks:
          continue
      else:
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      nevents = isvalid(fname) # check for corruption
      if nevents<0:
        if verbosity>=2:
          print ">>>   => Bad, nevents=%s"%(nevents)
        badchunks.append(ichunk)
        # TODO: remove file from outdir?
      else:
        if verbosity>=2:
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
  
  goodchunks.sort()
  pendchunks.sort()
  badchunks.sort()
  misschunks.sort()
  
  # PRINT
  def printchunks(jobden,label,text,col,show=False):
   if jobden:
     ratio = color("%4d/%d"%(len(jobden),noldchunks),col,bold=False)
     label = color(label,col,bold=True)
     jlist = (": "+', '.join(str(j) for j in jobden)) if show else ""
     print ">>> %s %s - %s%s"%(ratio,label,text,jlist)
   #else:
   #  print ">>> %2d/%d %s - %s"%(len(jobden),len(jobs),label,text)
  rtext = ""
  if ndasevents>0:
    ratio = 100.0*nprocevents/ndasevents
    rcol  = 'green' if ratio>90. else 'yellow' if ratio>80. else 'red'
    rtext = ": "+color("%d/%d (%d%%)"%(nprocevents,ndasevents,ratio),rcol,bold=True)
  printchunks(goodchunks,'SUCCES', "Chunks with output in outdir"+rtext,'green')
  printchunks(pendchunks,'PEND',"Chunks with pending or running jobs",'white',True)
  printchunks(badchunks, 'FAIL', "Chunks with corrupted output in outdir",'red',True)
  printchunks(misschunks,'MISS',"Chunks with no output in outdir",'red',True)
  
  return resubfiles, chunkdict
  
def isvalid(fname):
  """Check if a given file is valid, or corrupt."""
  nevts = -1
  file  = TFile.Open(fname,'READ')
  if file and not file.IsZombie():
    if file.GetListOfKeys().Contains('tree') and file.GetListOfKeys().Contains('cutflow'):
      nevts = file.Get('cutflow').GetBinContent(1)
      if nevts<=0:
        LOG.warning("Cutflow of file %r has nevts=%s<=0..."%(fname,nevts))
    if file.GetListOfKeys().Contains('Events'):
      nevts = file.Get('Events').GetEntries()
      if nevts<=0:
        LOG.warning("'Events' tree of file %r has nevts=%s<=0..."%(fname,nevts))
  return nevts
  


##################
#   (RE)SUBMIT   #
##################

def main_submit(args):
  """Submit or resubmit jobs to the batch system."""
  if args.verbosity>=1:
    print ">>> main_submit", args
  
  verbosity = args.verbosity
  force     = args.force #or True
  dryrun    = args.dryrun #or True
  batch     = getbatch(CONFIG,verb=verbosity+1)
  
  for jobcfg in preparejobs(args):
    cfgname = jobcfg['cfgname']
    jobdir  = jobcfg['jobdir']
    logdir  = jobcfg['logdir']
    outdir  = jobcfg['outdir']
    joblist = jobcfg['joblist']
    jobname = jobcfg['jobname']
    nchunks = jobcfg['nchunks']
    if nchunks<=0:
      print ">>>   Nothing to resubmit!"
      continue
    if batch.system=='HTCondor':
      script  = "python/batch/submit_HTCondor.sub"
      appcmds = ["initialdir=%s"%(jobdir),
                 "mylogfile='log/%s.$(ClusterId).$(ProcId).log'"%(jobname)]
      queue   = "arg from %s"%(joblist)
      option  = "" #-dry-run dryrun.log"
      jobid   = batch.submit(script,name=jobname,opt=option,app=appcmds,queue=queue,dry=dryrun)
    elif batch.system=='SLURM':
      script  = "python/batch/submit_SLURM.sh %s"%(joblist)
      logfile = os.path.join(logdir,"%x.%A.%a") # $JOBNAME.o$JOBID.$TASKID
      jobid   = batch.submit(script,name=jobname,log=logfile,array=nchunks,dry=dryrun)
    #elif batch.system=='SGE':
    else:
      LOG.throw(NotImplementedError,"Submission for batch system '%s' has not been implemented (yet)..."%(batch.system))
    
    ## SUBMIT
    #if args.force:
    #  jobid = batch.submit(*jargs,**jkwargs)
    #else:
    #  while True:
    #    submit = raw_input(">>> Do you also want to submit %d jobs to the batch system? [y/n] "%(nchunks))
    #    if any(s in submit.lower() for s in ['quit','exit']):
    #      exit(0)
    #    elif 'force' in submit.lower():
    #      submit = 'y'
    #      args.force = True
    #    if 'y' in submit.lower():
    #      jobid = batch.submit(*jargs,**jkwargs)
    #      break
    #    elif 'n' in submit.lower():
    #      print "Not submitting."
    #      break
    #    else:
    #      print "'%s' is not a valid answer, please choose y/n."%submit
    #print
    
    # WRITE JOBCONFIG
    jobcfg['jobids'].append(jobid)
    if verbosity>=1:
      print ">>> Creating config file '%s'..."%(cfgname)
    with open(cfgname,'w') as file:
      json.dump(jobcfg,file,indent=2)
  


#####################
#   STATUS & HADD   #
#####################

def main_status(args):
  """Check status of jobs (succesful/pending/failed/missing), or hadd job output."""
  if args.verbosity>=1:
    print ">>> main_status", args
  
  # SETTING
  eras           = args.eras
  channels       = args.channels
  tag            = args.tag
  checkdas       = args.checkdas
  checkqueue     = args.checkqueue
  dtypes         = args.dtypes
  filters        = args.samples
  vetoes         = args.vetoes
  force          = args.force
  hadd           = args.subcommand=='hadd'
  cleanup        = args.cleanup if hadd else False
  dryrun         = args.dryrun
  verbosity      = args.verbosity
  cmdverb        = max(1,verbosity)
  outdirformat   = CONFIG.outdir
  jobdirformat   = CONFIG.jobdir
  storedirformat = CONFIG.picodir
  jobs           = [ ]
  
  # LOOP over ERAS
  for era in eras:
    
    # LOOP over CHANNELS
    for channel in channels:
      print header("%s, %s"%(era,channel))
      
      # GET SAMPLES
      jobcfgs = repkey(os.path.join(jobdirformat,"config/jobconfig_$CHANNEL$TAG_try[0-9]*.json"),
                       ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag)
      if verbosity>=1:
        print ">>> %-12s = %s"%('cwd',os.getcwd())
        print ">>> %-12s = %s"%('jobcfgs',jobcfgs)
        print ">>> %-12s = %s"%('filters',filters)
        print ">>> %-12s = %s"%('vetoes',vetoes)
        print ">>> %-12s = %s"%('dtypes',dtypes)
      samples = getcfgsamples(jobcfgs,filter=filters,veto=vetoes,dtype=dtypes,verb=verbosity)
      if verbosity>=2:
        print ">>> Found samples: "+", ".join(repr(s.name) for s in samples)
      if hadd and 'skim' in channel:
        LOG.warning("Hadding into one file not available for skimming...")
        print
        continue
      
      # SAMPLE over SAMPLES
      found = False
      for sample in samples:
        if sample.channels and channel not in sample.channels: continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # CHECK JOBS ONLY ONCE
        if checkqueue==1 and not jobs:
          batch = getbatch(CONFIG,verb=verbosity)
          jobs  = batch.jobs(verb=verbosity-1)
        
        # HADD
        if hadd:
          jobdir   = sample.jobcfg['jobdir']
          outdir   = sample.jobcfg['outdir']
          storedir = repkey(storedirformat,ERA=era,CHANNEL=channel,TAG=tag,SAMPLE=sample.name,
                                           DAS=sample.paths[0].strip('/'),GROUP=sample.group)
          storage  = getstorage(storedir,ensure=True,verb=verbosity)
          outfile  = '%s_%s%s.root'%(sample.name,channel,tag)
          infiles  = os.path.join(outdir,'*_%s%s_[0-9]*.root'%(channel,tag))
          cfgfiles = os.path.join(sample.jobcfg['cfgdir'],'job*_%s%s_try[0-9]*.*'%(channel,tag))
          logfiles = os.path.join(sample.jobcfg['logdir'],'*_%s%s_try[0-9]*.*.*.log'%(channel,tag))
          if verbosity>=1:
            print ">>> Hadd'ing job output for '%s'"%(sample.name)
            print ">>> %-12s = %r"%('jobdir',jobdir)
            print ">>> %-12s = %r"%('outdir',outdir)
            print ">>> %-12s = %r"%('storedir',storedir)
            print ">>> %-12s = %s"%('infiles',infiles)
            print ">>> %-12s = %r"%('outfile',outfile)
          resubfiles, chunkdict = checkchuncks(sample,channel=channel,tag=tag,jobs=jobs,
                                               checkqueue=checkqueue,das=checkdas,verb=verbosity)
          if len(resubfiles)>0 and not force:
            LOG.warning("Cannot hadd job output because %d chunks need to be resubmitted..."%(len(resubfiles))+
                        "Please use -f or --force to hadd anyway.")
            continue
          #haddcmd = 'hadd -f %s %s'%(outfile,infiles)
          #haddout = execute(haddcmd,dry=dryrun,verb=max(1,verbosity))
          haddout = storage.hadd(infiles,outfile,dry=dryrun,verb=cmdverb)
          #os.system(haddcmd)
          
          # CLEAN UP
          # TODO: check if hadd was succesful with isvalid
          if cleanup:
            rmfiles   = ""
            rmfileset = [infiles,cfgfiles,logfiles]
            for files in rmfileset:
              if len(glob.glob(files))>0:
                rmfiles += ' '+files
            if verbosity>=2:
              print ">>> %-12s = %s"%('rmfileset',rmfileset)
              print ">>> %-12s = %s"%('rmfiles',rmfiles)
            if rmfiles:
              rmcmd = "rm %s"%(rmfiles)
              rmout = execute(rmcmd,dry=dryrun,verb=cmdverb)
        
        # ONLY CHECK STATUS
        else:
          outdir   = sample.jobcfg['outdir']
          if verbosity>=1:
            print ">>> Checking job status for '%s'"%(sample.name) 
            print ">>> %-12s = %r"%('outdir',outdir)
          checkchuncks(sample,channel=channel,tag=tag,jobs=jobs,
                       checkqueue=checkqueue,das=checkdas,verb=verbosity)
        
        print
      
      if not found:
        print ">>> Did not find any samples."
        print
  


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  parser = ArgumentParser(prog='run.py')
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                                help="set verbosity" )
  parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help='channel')
  parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help='year or era')
  parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="filter these samples; glob patterns (wildcards * and ?) are allowed." )
  parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ], action='store',
                          metavar='PATTERN',    help="exclude/veto this sample" )
  parser_sam.add_argument('--dtype',            dest='dtypes', choices=GLOB._dtypes, default=GLOB._dtypes, nargs='+',
                                                help='data type')
  parser_sam.add_argument('-D','--das',         dest='checkdas', default=False, action='store_true',
                                                help="check DAS for number of events" )
  parser_sam.add_argument('-t','--tag',         dest='tag', default="",
                                                help='tag for output')
  parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
                                                help='force overwrite')
  parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help='dry run for debugging purposes')
  parser_job = ArgumentParser(add_help=False,parents=[parser_sam])
  parser_job.add_argument('-p','--prefetch',    dest='prefetch', default=False, action='store_true',
                                                help="copy remote file during job to increase processing speed and ensure stability" )
  parser_job.add_argument('--test',             dest='testrun', action='store_true',
                                                help='run a test with limited nummer of jobs')
  parser_job.add_argument('--getjobs',          dest='checkqueue', type=int, nargs='?', const=1, default=-1, action='store',
                          metavar='N',          help="check job status: 0 (no check), 1 (check once), -1 (check every job)" ) # speed up if batch is slow
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
  #parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
  #                                              help='extra options for the batch system')
  parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=CONFIG.nfilesperjob,
                                                help='number of files per job')
  parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1, action='store',
                          metavar='N',          help="divide default number of files per job" )
  
  # SUBCOMMANDS
  subparsers = parser.add_subparsers(title="sub-commands",dest='subcommand',help="sub-command help")
  parser_ins = subparsers.add_parser('install',  parents=[parser_cmn], help='install')
  parser_get = subparsers.add_parser('get',      parents=[parser_sam], help='get information from configuration or samples')
  parser_set = subparsers.add_parser('set',      parents=[parser_cmn], help='set given variable in the configuration file')
  parser_chl = subparsers.add_parser('channel',  parents=[parser_lnk], help='link a channel to a module in the configuration file')
  parser_era = subparsers.add_parser('era',      parents=[parser_lnk], help='link an era to a sample list in the configuration file')
  parser_run = subparsers.add_parser('run',      parents=[parser_sam], help='run local post processor')
  parser_sub = subparsers.add_parser('submit',   parents=[parser_job], help='submit post-processing jobs')
  parser_res = subparsers.add_parser('resubmit', parents=[parser_job], help='resubmit failed post-processing jobs')
  parser_sts = subparsers.add_parser('status',   parents=[parser_chk], help='status of post-processing jobs')
  parser_hdd = subparsers.add_parser('hadd',     parents=[parser_chk], help='hadd post-processing job output')
  parser_get.add_argument('variable',           help='variable to change in the config file')
  parser_set.add_argument('variable',           help='variable to change in the config file')
  parser_set.add_argument('value',              help='value for given value')
  parser_set.add_argument('variable',           help='variable to get information on')
  parser_chl.add_argument('key',                metavar='channel', help='channel key name')
  parser_chl.add_argument('value',              metavar='module',  help='module linked to by given channel')
  parser_era.add_argument('key',                metavar='era',     help='era key name')
  parser_era.add_argument('value',              metavar='samples', help='samplelist linked to by given era')
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help='type of installation: standalone or compiled in CMSSW')
  #parser_hdd.add_argument('--keep',             dest='cleanup', default=True, action='store_false',
  #                                              help="do not remove job output after hadd'ing" )
  parser_hdd.add_argument('-r','--clean',       dest='cleanup', default=False, action='store_true',
                                                help="remove job output after hadd'ing" )
  parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                                                help='maximum number of events (per file) to process')
  parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
                                                help='maximum number of input files to process')
  parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
                                                help='number of samples to run')
  parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=CONFIG.filelistdir, default="", action='store',
                                                help="write file list, default = %r"%(CONFIG.filelistdir) )
                                                
  
  # ABBREVIATIONS
  args = sys.argv[1:]
  if args:
    subcmds = [ 
      'install','set','channel','era',
      'run','submit','resubmit','status','hadd',
    ]
    for subcmd in subcmds:
      if args[0] in subcmd[:len(args[0])]: # match abbreviation
        args[0] = subcmd
        break
  args = parser.parse_args(args)
  #args.testrun = True
  if hasattr(args,'tag') and len(args.tag)>=1 and args.tag[0]!='_':
    args.tag = '_'+args.tag
  
  # SUBCOMMAND MAINs
  os.chdir(CONFIG.basedir)
  if args.subcommand=='install':
    main_install(args)
  elif args.subcommand=='get':
    main_get(args)
  elif args.subcommand=='set':
    main_set(args)
  elif args.subcommand in ['channel','era']:
    main_link(args)
  elif args.subcommand=='run':
    main_run(args)
  elif args.subcommand in ['submit','resubmit']:
    main_submit(args)
  elif args.subcommand in ['status','hadd']:
    main_status(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  

