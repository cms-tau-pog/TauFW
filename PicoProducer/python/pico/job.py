#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, re, glob, json
from datetime import datetime
from collections import OrderedDict
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.common.tools.log import Logger, color, bold
from TauFW.common.tools.file import ensuredir, getline
from TauFW.common.tools.utils import execute, chunkify
from TauFW.common.tools.string import repkey, lreplace, alphanum_key
from TauFW.common.tools.LoadingBar import LoadingBar
from TauFW.PicoProducer.batch.utils import getbatch, getcfgsamples, chunkify_by_evts, evtsplitexp
from TauFW.PicoProducer.storage.utils import getstorage, getsamples, isvalid, itervalid, print_no_samples
from TauFW.PicoProducer.pico.run import getmodule
os.chdir(GLOB.basedir)
CONFIG = GLOB.getconfig(verb=0)
LOG    = Logger()



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
  dasfilters   = args.dasfilters   # filter (only include) these das paths (glob patterns)
  dasvetoes    = args.dasvetoes    # exclude these DAS paths (glob patterns)
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
  ncores       = args.ncores       # number of cores; validate output files in parallel
  verbosity    = args.verbosity
  jobs         = None
  
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
        samples = getsamples(era,channel=channel,tag=tag,dtype=dtypes,filter=filters,veto=vetoes,
                             dasfilter=dasfilters,dasveto=dasvetoes,moddict=moddict,verb=verbosity)
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
          cfgpattern = re.sub(r"(?<=try)\d+(?=.json(?:\.gz)?$)",r"*",cfgname)
          cfgnames   = [f for f in glob.glob(cfgpattern) if not f.endswith("_try1.json")]
          if cfgnames:
            LOG.warning("Job configurations for resubmission already exists! This can cause conflicting job output! "+
              "If you are sure you want to submit from scratch, please remove these files:\n>>>   "+"\n>>>   ".join(cfgnames))
        storage = getstorage(outdir,verb=verbosity,ensure=True)
        
        # GET FILES
        nevents = 0
        if resubmit: # resubmission
          if checkqueue==1 and jobs!=None: # check jobs only once to speed up performance
            batch = getbatch(CONFIG,verb=verbosity)
            jobs  = batch.jobs(verb=verbosity-1)
          infiles, chunkdict = checkchunks(sample,channel=channel,tag=tag,jobs=jobs,checkqueue=checkqueue,checkevts=checkevts,
                                           checkexpevts=checkexpevts,das=checkdas,ncores=ncores,verb=verbosity)[:2]
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
  pendjobs     = kwargs.get('jobs',         None  )
  checkdas     = kwargs.get('das',          True  ) # check number of events from DAS
  showlogs     = kwargs.get('showlogs',     False ) # print log files of failed jobs
  ncores       = kwargs.get('ncores',       4     ) # validate files in parallel
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
  elif verbosity>=2:
    print ">>> %-12s = %s"%('ndasevents',ndasevents)
  if verbosity>=3:
    print ">>> %-12s = %s"%('chunkdict',chunkdict)
  
  # CHECK PENDING JOBS
  if checkqueue<0 or pendjobs:
    if checkqueue!=1 or not pendjobs:
      batch = getbatch(CONFIG,verb=verbosity)
      pendjobs = batch.jobs(jobids,verb=verbosity-1) # refresh job list
    elif pendjobs:
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
    if pendjobs:
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
    outfiles  = storage.getfiles(filter=fpatterns,verb=verbosity-1) # get output files
    badfiles  = [ ]
    goodfiles = [ ]
    bar       = None # loading bar
    if verbosity<=1 and len(outfiles)>=15:
      bar = LoadingBar(len(outfiles),width=20,pre=">>> Checking output files: ",
                       message="files, 0/%d (0%%)"%(ndasevents),counter=True,remove=True)
    elif verbosity>=2:
      print ">>> %-12s = %s"%('pendchunks',pendchunks)
      print ">>> %-12s = %s"%('outfiles',outfiles)
    validated = itervalid(outfiles,checkevts=checkevts,ncores=ncores) # get number of events processed & check for corruption
    for nevents, fname in validated: # use validator for parallel processing
      if verbosity>=2:
        print ">>>   Checking job output '%s'..."%(fname)
      basename = os.path.basename(fname)
      infile   = chunkexp.sub(r"\1.root",basename) # reconstruct input file without path or postfix
      outmatch = chunkexp.match(basename)
      ipart    = int(outmatch.group(2) or -1) if outmatch else -1 # >0 if input file split by events
      ichunk   = -1
      matches  = [ ] # count how many times matched to chunk (if split by events)
      for i in chunkdict:
        if ichunk>-1: # already found corresponding input file in the previous iteration
          break
        for chunkfile in chunkdict[i]: # find chunk output file belongs to
          if infile not in chunkfile: continue
          matches.append(i)
          nevtsexp  = -1
          inmatch   = evtsplitexp.match(chunkfile) # filename:firstevt:maxevts
          if inmatch: # chunk was split by events
            firstevt = int(inmatch.group(2))
            maxevts  = int(inmatch.group(3))
            if firstevt/maxevts!=ipart: # right file, wrong chunk
              if verbosity>=3:
                print ">>>   Not in chunk %d, %r"%(i,chunkfile)
              continue
            if checkexpevts or verbosity>=2:
              filentot = filenevts.get(inmatch.group(1),-1)
              if filentot>-1 and firstevt>=filentot: # sanity check
                LOG.warning("checkchunks: chunk %d has firstevt=%s>=%s=filentot, which indicates a bug or changed input file %s."%(
                  ichunk,firstevt,filentot,chunkfile))
              nevtsexp = min(maxevts,filentot-firstevt) if filentot>-1 else maxevts # = maxevts; roughly expected nevts (some loss due to cuts)
          elif checkexpevts or verbosity>=2:
            nevtsexp = filenevts.get(chunkfile,-1) # expected number of processed events
          ichunk = i
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
              if nevtsexp>0:
                frac = "%.1f%%"%(100.0*nevents/nevtsexp) if nevtsexp!=0 else ""
                print ">>>   => Good, nevents=%s/%s %s"%(nevents,nevtsexp,frac)
              else:
                print ">>>   => Good, nevents=%s"%(nevents)
            nprocevents += nevents
            goodfiles.append(chunkfile)
      if verbosity>=2:
        if ichunk<0:
          if matches:
            print ">>>   => No match with input file (ipart=%d, but found in %d chunks; %s)..."%(ipart,len(matches),matches)
          else:
            print ">>>   => No match with input file..."
        #LOG.warning("Did not recognize output file '%s'!"%(fname))
        continue
      if bar:
        status = "files, %s/%s events (%d%%)"%(nprocevents,ndasevents,100.0*nprocevents/ndasevents) if ndasevents>0 else ""
        bar.count(status)
    
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
    if pendjobs:
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
    bar      = None # loading bar
    if verbosity<=1 and len(outfiles)>=15:
      bar = LoadingBar(len(outfiles),width=20,pre=">>> Checking output files: ",
                       message="files, 0/%d (0%%)"%(ndasevents),counter=True,remove=True)
    elif verbosity>=2:
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
          for chunkfile in chunkdict[ichunk]: # count events for each input file in this chunk
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
              nevtsexp += filenevts.get(chunkfile,0)
          if checkexpevts and nevtsexp>0 and nevents!=nevtsexp:
            LOG.warning("checkchunks: Found %s processed events, but expected %s for %s..."%(nevents,nevtsexp,fname))
        if verbosity>=2:
          if nevtsexp>0:
            frac = "%.1f%%"%(100.0*nevents/nevtsexp) if nevtsexp!=0 else ""
            print ">>>   => Good, nevents=%d/%d %s"%(nevents,nevtsexp,frac)
          else:
            print ">>>   => Good, nevents=%s"%(nevents)
        nprocevents += nevents
        goodchunks.append(ichunk)
      if bar:
        status = "files, %s/%s events (%d%%)"%(nprocevents,ndasevents,100.0*nprocevents/ndasevents) if ndasevents>0 else ""
        bar.count(status)
    
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
      if 'etp' in GLOB.host:
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
      if cfgname.endswith(".json.gz"):
        with gzip.open(cfgname,'wt') as file:
          file.write(json.dump(jobcfg),indent=2)
      else:
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
  eras           = args.eras         # eras to loop over and run
  channels       = args.channels     # channels to loop over and run
  tag            = args.tag
  checkdas       = args.checkdas     # check number of events from DAS
  checkqueue     = args.checkqueue   # check queue of batch system for pending jobs
  checkevts      = args.checkevts    # validate output file & count events (slow, default)
  checkexpevts   = args.checkexpevts # compare actual to expected number of processed events
  dtypes         = args.dtypes       # filter (only include) these sample types ('data','mc','embed')
  filters        = args.samples      # filter (only include) these samples (glob patterns)
  dasfilters     = args.dasfilters   # filter (only include) these das paths (glob patterns)
  vetoes         = args.vetoes       # exclude these sample (glob patterns)
  dasvetoes      = args.dasvetoes    # exclude these DAS paths (glob patterns)
  force          = args.force
  subcmd         = args.subcommand
  cleanup        = subcmd=='clean' or (subcmd=='hadd' and args.cleanup)
  maxopenfiles   = args.maxopenfiles if subcmd=='hadd' else 0 # maximum number of files opened during hadd, via -n option
  dryrun         = args.dryrun       # run through routine without actually executing hadd, rm, ...
  ncores         = args.ncores       # number of cores; validate output files in parallel
  verbosity      = args.verbosity
  cmdverb        = max(1,verbosity)
  outdirformat   = CONFIG.outdir
  jobdirformat   = CONFIG.jobdir
  storedirformat = CONFIG.picodir
  jobs           = None
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
                       ERA=era,SAMPLE='*',GROUP='*',CHANNEL=channel,TAG=tag) # get ALL job configs
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
        channel_ = channel
        if channel=='*': # grab channel from job config name
          matches = re.findall(r"config/jobconfig_(\w+)%s_try\d+.json(?:\.gz)?"%(tag),sample.jobcfg['config'])
          if matches:
            channel_ = matches[0]
        elif sample.channels and channel_ not in sample.channels:
          continue
        found = True
        print ">>> %s"%(bold(sample.name))
        for path in sample.paths:
          print ">>> %s"%(bold(path))
        
        # CHECK JOBS ONLY ONCE
        if checkqueue==1 and jobs!=None:
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
          storedir = repkey(storedirformat,ERA=era,CHANNEL=channel_,TAG=tag,SAMPLE=sample.name,
                                           DAS=sample.paths[0].strip('/'),GROUP=sample.group)
          storage  = getstorage(storedir,ensure=True,verb=verbosity)
          outfile  = '%s_%s%s.root'%(sample.name,channel_,tag)
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
          resubfiles, chunkdict, npend = checkchunks(sample,channel=channel_,tag=tag,jobs=jobs,checkqueue=checkqueue,checkevts=checkevts,
                                                     das=checkdas,checkexpevts=checkexpevts,ncores=ncores,verb=verbosity)
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
          checkchunks(sample,channel=channel_,tag=tag,jobs=jobs,showlogs=showlogs,checkqueue=checkqueue,
                      checkevts=checkevts,das=checkdas,ncores=ncores,verb=verbosity)
        
        print
      
      if not found:
        print_no_samples(dtypes,filters,vetoes,jobdir_,jobcfgs)
  

