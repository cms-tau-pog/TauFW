#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
import os, sys, glob, json
#import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import TauFW.PicoProducer.tools.config as GLOB
from TauFW.common.tools.file import ensurefile, ensureinit
from TauFW.common.tools.string import repkey, rreplace
from TauFW.common.tools.log import Logger, color, bold
from TauFW.PicoProducer.analysis.utils import ensuremodule
from TauFW.PicoProducer.storage.utils import getsamples
from TauFW.PicoProducer.storage.utils import LOG as SLOG
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
  


############
#   LIST   #
############

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
  eras       = args.eras       # eras to loop over and run
  channels   = args.channels or [""] # channels to loop over and run
  dtypes     = args.dtypes     # filter (only include) these sample types ('data','mc','embed')
  filters    = args.samples    # filter (only include) these samples (glob patterns)
  dasfilters = args.dasfilters # filter (only include) these das paths (glob patterns)
  vetoes     = args.vetoes     # exclude these sample (glob patterns)
  dasvetoes  = args.dasvetoes  # exclude these DAS paths (glob patterns)
  inclurl    = args.inclurl    # include URL in filelist
  checkdas   = args.checkdas or args.dasfiles # check file list in DAS
  checklocal = args.checklocal # check nevents in local files
  split      = args.split      # split samples with multiple DAS dataset paths
  limit      = args.limit
  writedir   = args.write      # write sample file list to text file
  tag        = args.tag
  ncores     = args.ncores     # number of cores to get nevents in parallel
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
    print ">>> %-14s = %s"%('checkdas',checkdas)
    print ">>> %-14s = %s"%('checklocal',checklocal)
    print ">>> %-14s = %s"%('split',split)
    print ">>> %-14s = %s"%('limit',limit)
    print ">>> %-14s = %s"%('writedir',writedir)
    print ">>> %-14s = %s"%('ncores',ncores)
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
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                             dasfilter=dasfilters,dasveto=dasvetoes,verb=verbosity)
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
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                             dasfilter=dasfilters,dasveto=dasvetoes,split=split,verb=verbosity)
        
        # LOOP over SAMPLES
        for sample in samples:
          print ">>> %s"%(bold(sample.name))
          for path in sample.paths:
            print ">>> %s"%(bold(path))
          if getnevts or checkdas or checklocal:
            das     = checkdas and not checklocal # checklocal overrides checkdas
            refresh = das # (not sample.storage and all('/store' in f for f in sample.files)
            nevents = sample.getnevents(das=das,refresh=refresh,verb=verbosity+1)
            storage = "(%s)"%sample.storage.__class__.__name__ if checklocal else "(DAS)" if checkdas else ""
            print ">>>   %-7s = %s %s"%('nevents',nevents,storage)
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
            sample.writefiles(flistname,nevts=getnevts,ncores=ncores)
  
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
  eras       = args.eras       # eras to loop over and run
  channels   = args.channels or [""] # channels to loop over and run
  dtypes     = args.dtypes     # filter (only include) these sample types ('data','mc','embed')
  filters    = args.samples    # filter (only include) these samples (glob patterns)
  dasfilters = args.dasfilters # filter (only include) these das paths (glob patterns)
  vetoes     = args.vetoes     # exclude these sample (glob patterns)
  dasvetoes  = args.dasvetoes  # exclude these DAS paths (glob patterns)
  checkdas   = args.checkdas or args.dasfiles # check file list in DAS
  split      = args.split      # split samples with multiple DAS dataset paths
  retries    = args.retries    # retry if error is thrown
  getnevts   = args.getnevts   # check nevents in local files
  ncores     = args.ncores   # number of cores to get nevents in parallel
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
      samples0 = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                            dasfilter=dasfilters,dasveto=dasvetoes,split=split,verb=verbosity)
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
          sample.filelist = None # do not load from existing text file; overwrite existing ones
          for path in sample.paths:
            print ">>> %s"%(bold(path))
          #infiles = sample.getfiles(das=checkdas,url=inclurl,limit=limit,verb=verbosity+1)
          flistname = repkey(listname,ERA=era,GROUP=sample.group,SAMPLE=sample.name) #,TAG=tag
          try:
            sample.writefiles(flistname,nevts=getnevts,das=checkdas,refresh=checkdas,ncores=ncores,verb=verbosity)
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
    


############
#   MAIN   #
############

if __name__ == "__main__":
  
  # COMMON
  from argparse import ArgumentParser
  description = "Central script to process nanoAOD for skimming or analysis."
  parser = ArgumentParser(prog='pico.py',description=description,epilog="Good luck!")
  parser_cmn = ArgumentParser(add_help=False)
  parser_cmn.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0,
                                                help="set verbosity")
  parser_sam = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_lnk = ArgumentParser(add_help=False,parents=[parser_cmn])
  parser_sam.add_argument('-c','--channel',     dest='channels', choices=CONFIG.channels.keys(), default=[ ], nargs='+',
                                                help="skimming or analysis channel to run")
  parser_sam.add_argument('-y','-e','--era',    dest='eras', choices=CONFIG.eras.keys(), default=[ ], nargs='+',
                                                help="year or era to specify the sample list")
  parser_sam.add_argument('-s', '--sample',     dest='samples', type=str, nargs='+', default=[ ],
                          metavar='PATTERN',    help="filter these samples; glob patterns like '*' and '?' wildcards are allowed")
  parser_sam.add_argument('-Z', '--dasfilter',  dest='dasfilters', type=str, nargs='+', default=[ ],
                          metavar='PATTERN',    help="filter these DAS paths; glob patterns like '*' and '?' wildcards are allowed")
  parser_sam.add_argument('-x', '--veto',       dest='vetoes', nargs='+', default=[ ],
                          metavar='PATTERN',    help="exclude/veto these samples; glob patterns are allowed")
  parser_sam.add_argument('-X', '--dasveto',    dest='dasvetoes', nargs='+', default=[ ],
                          metavar='PATTERN',    help="exclude/veto these DAS paths; glob patterns are allowed")
  parser_sam.add_argument('--dtype',            dest='dtypes', choices=GLOB.dtypes, default=GLOB.dtypes, nargs='+',
                                                help="filter these data type(s)")
  parser_sam.add_argument('-D','--das',         dest='checkdas', action='store_true',
                                                help="check DAS for total number of events")
  parser_sam.add_argument('--dasfiles',         dest='dasfiles', action='store_true',
                                                help="get files from DAS (instead of local storage, if predefined)")
  parser_sam.add_argument('-t','--tag',         dest='tag', default="",
                                                help="tag for output file name")
  parser_sam.add_argument('-f','--force',       dest='force', action='store_true',
                                                help="force overwrite")
  parser_sam.add_argument('-d','--dry',         dest='dryrun', action='store_true',
                                                help="dry run: prepare job without submitting for debugging purposes")
  parser_sam.add_argument('-E', '--opts',       dest='extraopts', type=str, nargs='+', default=[ ],
                          metavar='KEY=VALUE',  help="extra options for the skim or analysis module, "
                                                     "passed as list of 'KEY=VALUE', separated by spaces")
  parser_sam.add_argument('-C','--ncores',      dest='ncores', type=int, default=CONFIG.ncores,
                                                help="number of cores to run event checks or validation in parallel")
  parser_job = ArgumentParser(add_help=False,parents=[parser_sam])
  parser_job.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during job to increase processing speed and ensure stability")
  parser_job.add_argument('-T','--test',        dest='testrun', type=int, nargs='?', const=10000, default=0,
                          metavar='NEVTS',      help="run a test with limited nummer of jobs and events, default nevts=%(const)d")
  parser_job.add_argument('--checkqueue',       dest='checkqueue', type=int, nargs='?', const=1, default=-1,
                          metavar='N',          help="check job status: 0 (no check), 1 (check once, fast), -1 (check every job, slow, default)") # speed up if batch is slow
  parser_job.add_argument('--skipevts',         dest='checkevts', action='store_false',
                                                help="skip validation and counting of events in output files (faster)")
  parser_job.add_argument('--checkexpevts',     dest='checkexpevts', action='store_true', default=None,
                                                help="check if the actual number of processed events is the same as the expected number")
  parser_chk = ArgumentParser(add_help=False,parents=[parser_job])
  parser_job.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
                                                help="extra options for the batch system")
  parser_job.add_argument('-M','--time',        dest='time', default=None,
                                                help="maximum run time of job")
  parser_job.add_argument('-q','--queue',       dest='queue', default=str(CONFIG.queue),
                                                help="queue of batch system (job flavor on HTCondor)")
  parser_job.add_argument('-P','--prompt',      dest='prompt', action='store_true',
                                                help="ask user permission before submitting a sample")
  parser_job.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help="preselection to be shipped to skimjob.py during run command")
  parser_job.add_argument('-n','--filesperjob', dest='nfilesperjob', type=int, default=-1,
                                                help="number of files per job, default=%d"%(CONFIG.nfilesperjob))
  parser_job.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=-1,
                          metavar='NEVTS',      help="maximum number of events per job to process (split large files), default=%d"%(CONFIG.maxevtsperjob))
  parser_job.add_argument('--split',            dest='split_nfpj', type=int, nargs='?', const=2, default=1,
                          metavar='NFILES',     help="divide default number of files per job, default=%(const)d")
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
  parser_get.add_argument('variable',           help="variable to get information on",choices=['samples','files','nevents','nevts',]+CONFIG.keys())
  parser_set.add_argument('variable',           help="variable to set or change in the config file")
  parser_set.add_argument('key',                help="channel or era key name", nargs='?', default=None)
  parser_set.add_argument('value',              help="value for given value")
  parser_wrt.add_argument('listname',           help="file name of text file for file list, default=%(default)r", nargs='?', default=str(CONFIG.filelistdir))
  parser_rmv.add_argument('variable',           help="variable to remove from the config file")
  parser_rmv.add_argument('key',                help="channel or era key name to remove", nargs='?', default=None)
  parser_chl.add_argument('key',                metavar='channel', help="channel key name")
  parser_chl.add_argument('value',              metavar='module',  help="module linked to by given channel")
  parser_era.add_argument('key',                metavar='era',     help="era key name")
  parser_era.add_argument('value',              metavar='samples', help="samplelist linked to by given era")
  parser_ins.add_argument('type',               choices=['standalone','cmmsw'], #default=None,
                                                help="type of installation: standalone or compiled in CMSSW")
  parser_get.add_argument('-U','--url',         dest='inclurl', action='store_true',
                                                help="include XRootD url in filename for 'get files'")
  parser_get.add_argument('-L','--limit',       dest='limit', type=int, default=-1,
                          metavar='NFILES',     help="limit number files in list for 'get files'")
  parser_get.add_argument('-l','--local',       dest='checklocal', action='store_true',
                                                help="compute total number of events in storage system (not DAS) for 'get files' or 'get nevents'")
  parser_get.add_argument('-w','--write',       dest='write', type=str, nargs='?', const=str(CONFIG.filelistdir), default="",
                          metavar='FILE',       help="write file list, default=%(const)r")
  parser_get.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)")
  parser_wrt.add_argument('-n','--nevts',       dest='getnevts', action='store_true',
                                                help="get nevents per file")
  parser_wrt.add_argument('-S','--split',       dest='split', action='store_true',
                                                help="split samples with multiple datasets (extensions)")
  parser_wrt.add_argument('-T','--try',         dest='retries', type=int, default=1, action='store',
                                                help="number of retries if file is not found")
  parser_run.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                          metavar='NEVTS',      help="maximum number of events (per file) to process")
  parser_run.add_argument('--preselect',        dest='preselect', type=str, default=None,
                                                help="preselection to be shipped to skimjob.py during run command")
  parser_run.add_argument('-n','--nfiles',      dest='nfiles', type=int, default=1,
                                                help="maximum number of input files to process (per sample), default=%(default)d")
  parser_run.add_argument('-S', '--nsamples',   dest='nsamples', type=int, default=1,
                                                help="number of samples to run, default=%(default)d")
  parser_run.add_argument('-i', '--input',      dest='infiles', nargs='+', default=[ ],
                                                help="input files (nanoAOD)")
  parser_run.add_argument('-o', '--outdir',     dest='outdir', type=str, default='output',
                                                help="output directory, default=%(default)r")
  parser_run.add_argument('-p','--prefetch',    dest='prefetch', action='store_true',
                                                help="copy remote file during run to increase processing speed and ensure stability")
  parser_sts.add_argument('-l','--log',         dest='showlogs', type=int, nargs='?', const=-1, default=0,
                          metavar='NLOGS',      help="show log files of failed jobs: 0 (show none), -1 (show all), n (show max n)")
  #parser_hdd.add_argument('--keep',             dest='cleanup', action='store_false',
  #                                              help="do not remove job output after hadd'ing")
  parser_hdd.add_argument('-m','--maxopenfiles',dest='maxopenfiles', type=int, default=CONFIG.maxopenfiles,
                          metavar='NFILES',     help="maximum numbers to be opened during hadd, default=%(default)d")
  parser_hdd.add_argument('-r','--clean',       dest='cleanup', action='store_true',
                                                help="remove job output (to be used after hadd'ing)")
  
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
    
  # VERBOSITY
  if args.verbosity>=2:
    SLOG.setverbosity(args.verbosity-1)
  
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
    from TauFW.PicoProducer.pico.run import main_run
    main_run(args)
  elif args.subcommand in ['submit','resubmit']:
    from TauFW.PicoProducer.pico.job import main_submit
    main_submit(args)
  elif args.subcommand in ['status','hadd','clean']:
    from TauFW.PicoProducer.pico.job import main_status
    main_status(args)
  else:
    print ">>> subcommand '%s' not implemented!"%(args.subcommand)
  
  print ">>> Done!"
  

