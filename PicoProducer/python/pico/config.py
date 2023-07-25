# Author: Izaak Neutelings (February 2022)
from past.builtins import basestring # for python2 compatibility
import os, glob, json
from TauFW.common.tools.file import ensurefile, ensureinit
from TauFW.common.tools.string import repkey, rreplace, lreplace
from TauFW.PicoProducer.analysis.utils import ensuremodule
from TauFW.PicoProducer.storage.utils import getsamples
from TauFW.PicoProducer.pico.common import *



############
#   LIST   #
############

def main_list(args):
  """List contents of configuration for those lazy to do 'cat config/config.json'."""
  if args.verbosity>=1:
    print(">>> main_list", args)
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print('-'*80)
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('config',CONFIG))
    print('-'*80)
  
  print(">>> Configuration %s:"%(cfgname))
  for variable, value in CONFIG.items():
    variable = "'"+color(variable)+"'"
    if isinstance(value,dict):
      print(">>>  %s:"%(variable))
      for key, item in value.items():
        if isinstance(item,basestring): item = str(item)
        print(">>>    %-12r -> %r"%(str(key),str(item)))
    else:
      if isinstance(value,basestring): value = str(value)
      print(">>>  %-24s = %r"%(variable,value))
  


###########
#   GET   #
###########

def main_get(args):
  """Get information of given variable in configuration or samples."""
  if args.verbosity>=1:
    print(">>> main_get", args)
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
    print('-'*80)
    print(">>> %-14s = %s"%('variable',variable))
    print(">>> %-14s = %s"%('eras',eras))
    print(">>> %-14s = %s"%('channels',channels))
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('config',CONFIG))
    print(">>> %-14s = %s"%('checkdas',checkdas))
    print(">>> %-14s = %s"%('checklocal',checklocal))
    print(">>> %-14s = %s"%('split',split))
    print(">>> %-14s = %s"%('limit',limit))
    print(">>> %-14s = %s"%('writedir',writedir))
    print(">>> %-14s = %s"%('ncores',ncores))
    print('-'*80)
  
  # LIST SAMPLES
  if variable=='samples':
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        if channel:
          print(">>> Getting file list for era %r, channel %r"%(era,channel))
        else:
          print(">>> Getting file list for era %r"%(era))
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                             dasfilter=dasfilters,dasveto=dasvetoes,verb=verbosity)
        if not samples:
          LOG.warning("No samples found for era %r."%(era))
        for sample in samples:
          print(">>> %s"%(bold(sample.name)))
          for path in sample.paths:
            print(">>>   %s"%(path))
  
  # LIST SAMPLE FILES
  elif variable in ['files','nevents','nevts']:
    
    # LOOP over ERAS & CHANNELS
    if not eras:
      LOG.warning("Please specify an era to get a sample for.")
    for era in eras:
      for channel in channels:
        target = "file list" if variable=='files' else "nevents"
        if channel:
          print(">>> Getting %s for era %r, channel %r"%(target,era,channel))
        else:
          print(">>> Getting %s for era %r"%(target,era))
        print(">>> ")
        
        # GET SAMPLES
        LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
        samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                             dasfilter=dasfilters,dasveto=dasvetoes,split=split,verb=verbosity)
        
        # LOOP over SAMPLES
        for sample in samples:
          print(">>> %s"%(bold(sample.name)))
          for path in sample.paths:
            print(">>> %s"%(bold(path)))
          if getnevts or checkdas or checklocal:
            das     = checkdas and not checklocal # checklocal overrides checkdas
            refresh = das # (not sample.storage and all('/store' in f for f in sample.files)
            nevents = sample.getnevents(das=das,refresh=refresh,verb=verbosity+1)
            storage = "(%s)"%sample.storage.__class__.__name__ if checklocal else "(DAS)" if checkdas else ""
            print(">>>   %-7s = %s %s"%('nevents',nevents,storage))
          if variable=='files':
            infiles = sample.getfiles(das=checkdas,url=inclurl,limit=limit,verb=verbosity+1)
            print(">>>   %-7s = %r"%('channel',channel))
            print(">>>   %-7s = %r"%('url',sample.url))
            print(">>>   %-7s = %r"%('postfix',sample.postfix))
            print(">>>   %-7s = %s"%('nfiles',len(infiles)))
            print(">>>   %-7s = [ "%('infiles'))
            for file in infiles:
              print(">>>     %r"%file)
            print(">>>   ]")
          print(">>> ")
          if writedir: # write files to text files
            sample.filelist = None # do not load from existing text file; overwrite existing ones
            flistname = repkey(writedir,ERA=era,GROUP=sample.group,SAMPLE=sample.name,TAG=tag)
            print(">>> Write list to %r..."%(flistname))
            sample.writefiles(flistname,nevts=getnevts,das=checkdas,refresh=checkdas,ncores=ncores,verb=verbosity)
  
  # CONFIGURATION
  else:
    if variable in CONFIG:
      print(">>> Configuration of %r: %s"%(variable,color(CONFIG[variable])))
    else:
      print(">>> Did not find %r in the configuration"%(variable))
  


#############
#   WRITE   #
#############

def main_write(args):
  """Get information of given variable in configuration or samples."""
  if args.verbosity>=1:
    print(">>> main_write", args)
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
  skipempty  = args.skipempty  # do not write empty events
  ncores     = args.ncores     # number of cores to get nevents in parallel
  verbosity  = args.verbosity
  cfgname    = CONFIG._path
  if verbosity>=1:
    print('-'*80)
    print(">>> %-14s = %s"%('listname',listname))
    print(">>> %-14s = %s"%('getnevts',getnevts))
    print(">>> %-14s = %s"%('eras',eras))
    print(">>> %-14s = %s"%('channels',channels))
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('config',CONFIG))
    print('-'*80)
  
  # LOOP over ERAS & CHANNELS
  if not eras:
    LOG.warning("Please specify an era to get a sample for.")
  for era in eras:
    for channel in channels:
      info = ">>> Getting file list for era %r"%(era)
      if channel:
        info += ", channel %r"%(channel)
      print(info)
      print(">>> ")
      
      LOG.insist(era in CONFIG.eras,"Era '%s' not found in the configuration file. Available: %s"%(era,CONFIG.eras))
      samples0 = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes,
                            dasfilter=dasfilters,dasveto=dasvetoes,split=split,verb=verbosity)
      sampleset = [samples0]
      for retry in range(retries):
        sampleset.append([ ]) # list for retries
      if len(samples0)>=2 and '$' not in listname.replace('$ERA',''):
        LOG.warn("Given list name %r without variables for %d samples. "%(listname,len(samples0))+
                 "Note this will overwrite. Please add variables, such as '$SAMPLE', '$PATH', '$GROUP'.")
      
      # LOOP over SAMPLES
      for retry, samples in enumerate(sampleset):
        if not samples:
          break
        if retry>0 and len(samples0)>1:
          if retries>=2:
            print(">>> Retry %d/%d: %d/%d samples...\n>>>"%(retry,retries,len(samples),len(samples0)))
          else:
            print(">>> Trying again %d/%d samples...\n>>>"%(len(samples),len(samples0)))
        for sample in samples:
          print(">>> %s"%(bold(sample.name)))
          sample.filelist = None # do not load from existing text file; overwrite existing ones
          for path in sample.paths:
            print(">>> %s"%(bold(path)))
          #infiles = sample.getfiles(das=checkdas,url=inclurl,limit=limit,verb=verbosity+1)
          flistname = repkey(listname,ERA=era,GROUP=sample.group,SAMPLE=sample.name) #,TAG=tag
          try:
            sample.writefiles(flistname,nevts=getnevts,skipempty=skipempty,das=checkdas,refresh=checkdas,ncores=ncores,verb=verbosity)
          except IOError as err: # one of the ROOT file could not be opened
            print("IOError: "+err.message)
            if retry<retries and sample not in sampleset[retry+1]: # try again after the others
              print(">>> Will try again...")
              sampleset[retry+1].append(sample)
          print(">>> ")
  


###########
#   SET   #
###########

def main_set(args):
  """Set variables in the config file."""
  global CONFIG
  if args.verbosity>=1:
    print(">>> main_set", args)
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
    print('-'*80)
  print(">>> Setting variable '%s' to '%s' config"%(color(variable),value))
  if verbosity>=1:
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('config',CONFIG))
    print('-'*80)
  if variable=='all':
    if 'default' in value:
      CONFIG = GLOB.setdefaultconfig(verb=args.verbosity)
      CONFIG.write(backup=False)
    else:
      LOG.warning("Did not recognize value '%s'. Did you mean 'default'?"%(value))
  elif variable in ['nfilesperjob','maxevtsperjob','maxopenfiles','ncores'] or type(CONFIG[variable])==int:
    CONFIG[variable] = int(value)
    CONFIG.write(backup=True)
  else:
    CONFIG[variable] = value
    CONFIG.write(backup=True)
  


############
#   LINK   #
############

def main_link(args):
  """Link channels or eras in the config file."""
  if args.verbosity>=1:
    print(">>> main_link", args)
  variable  = args.subcommand
  varkey    = variable+'s'
  key       = args.key
  value     = args.value
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print('-'*80)
  print(">>> Linking %s '%s' to '%s' in the configuration..."%(variable,color(key),value))
  if verbosity>=1:
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('key',key))
    print(">>> %-14s = %s"%('value',value))
    print(">>> %-14s = %s"%('config',CONFIG))
    print('-'*80)
  
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
      ensureinit(path,by="pico.py") # ensure an __init__.py exists in path
      modobj = ensuremodule(module)
      modpath = lreplace(os.path.relpath(modobj.__file__),"../../../python/TauFW/PicoProducer/")
      print(">>> Linked to %s"%(modpath))
      value  = ' '.join([module]+parts[1:])
  elif varkey=='eras':
    if 'samples/' in value: # useful for tab completion
      value = ''.join(value.split('samples/')[1:])
    path = os.path.join("samples",repkey(value,ERA='*',CHANNEL='*',TAG='*'))
    LOG.insist(glob.glob(path),"Did not find any sample lists '%s'"%(path))
    ensureinit(os.path.dirname(path),by="pico.py") # ensure an __init__.py exists in path
  if value!=oldval:
    print(">>> Converted '%s' to '%s'"%(oldval,value))
  CONFIG[varkey][key] = value
  CONFIG.write(backup=True)
  


##############
#   REMOVE   #
##############

def main_rm(args):
  """Remove variable from the config file."""
  if args.verbosity>=1:
    print(">>> main_rm", args)
  variable  = args.variable
  key       = args.key # 'channel' or 'era'
  verbosity = args.verbosity
  cfgname   = CONFIG._path
  if verbosity>=1:
    print('-'*80)
  if key:
    print(">>> Removing %s '%s' from the configuration..."%(variable,color(key)))
  else:
    print(">>> Removing variable '%s' from the configuration..."%(color(variable)))
  if verbosity>=1:
    print(">>> %-14s = %s"%('variable',variable))
    print(">>> %-14s = %s"%('key',key))
    print(">>> %-14s = %s"%('cfgname',cfgname))
    print(">>> %-14s = %s"%('config',CONFIG))
    print('-'*80)
  if key: # redirect 'channel' and 'era' keys to main_link
    variable = variable+'s'
    if variable in CONFIG:
      if key in CONFIG[variable]:
        CONFIG[variable].pop(key,None)
        CONFIG.write(backup=True)
      else:
        print(">>> %s '%s' not in the configuration. Nothing to remove..."%(variable.capitalize(),key))
    else:
      print(">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable))
  else:
    if variable in CONFIG:
      CONFIG.pop(variable)
      CONFIG.write(backup=True)
    else:
      print(">>> Variable '%s' not in the configuration. Nothing to remove..."%(variable))
    
