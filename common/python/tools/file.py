# Author: Izaak Neutelings (May 2020)
import os, re, shutil
import importlib, traceback
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from TauFW.common.tools.log import LOG
from TauFW.common.tools.utils import ensurelist
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))


def writetemplate(templatename,outfilename,sublist=[],rmlist=[],applist=[],**kwargs):
  """Write file from template."""
  sublist = [(re.compile("\$%s(?!\w)"%p),str(v)) for p, v in sublist]
  with open(templatename,'r') as template:
    with open(outfilename,'w') as file:
      for i, line in enumerate(template.readlines()):
        #linenum = "L%d:"%i
        if any(r in line for r in rmlist):
          continue # skip line
        for regexp, value in sublist:
          #pattern = '$'+pattern
          if regexp.search(line):
            #line = line.replace(pattern,str(value))
            line = regexp.sub(value,line)
        file.write(line)
      for line in ensurelist(applist):
        file.write(line+'\n') # append
  

def ensuredir(*dirnames,**kwargs):
  """Make directory if it does not exist.
  If more than one path is given, it is joined into one."""
  dirname   = os.path.join(*dirnames)
  empty     = kwargs.get('empty', False)
  verbosity = kwargs.get('verb',  0    )
  if not dirname:
    pass
  elif not os.path.exists(dirname):
    os.makedirs(dirname)
    if verbosity>=1:
      print '>>> Made directory "%s"'%(dirname)
    if not os.path.exists(dirname):
      print '>>> Failed to make directory "%s"'%(dirname)
  elif empty:
    for filename in os.listdir(dirname):
      filepath = os.path.join(dirname,filename)
      if os.path.isfile(filepath) or os.path.islink(filepath):
        os.unlink(filepath)
      elif os.path.isdir(filepath):
        shutil.rmtree(filepath)
  return dirname
  

def ensurefile(*paths,**kwargs):
  """Ensure file exists.
  If more than one path is given, it is joined into one."""
  fatal = kwargs.get('fatal',True)
  path = os.path.join(*paths)
  if not os.path.isfile(path):
    if fatal:
      raise IOError("Did not find file %s."%(path))
    else:
      print ">>> Warning! Did not find file %s."%(path)
  return path
  

def ensuremodule(modname,package):
  """Ensure Sample method exists in python/methods.
  E.g. module = ensuremodule(modname,"PicoProducer.analysis")"""
  # TODO: absolute path
  modfile  = ensurefile(basedir,package.replace('.','/python/',1),"%s.py"%(modname.replace('.','/')))
  modpath  = "TauFW.%s.%s"%(package,modname) #modfile.replace('.py','').replace('/','.')
  modclass = modname.split('.')[-1]
  try:
    module = importlib.import_module(modpath)
  except Exception as err:
    print traceback.format_exc()
    LOG.throw(ImportError,"Importing module '%s' failed. Please check %s! cwd=%r"%(modpath,modfile,os.getcwd()))
  if not hasattr(module,modclass):
    LOG.throw(IOError,"Module '%s' in %s does not have a module named '%s'!"%(module,modfile,modname))
  return module
  

def rmfile(filepaths):
  """Remove (list of) files."""
  if isinstance(filepaths,str):
    filepaths = [filepaths]
  for filepath in filepaths:
    if os.path.isfile(filepath):
      os.unlink(filepath)
  

def getline(fname,iline):
  target = ""
  with open(fname) as file:
    for i, line in enumerate(file):
      if i==iline:
        target = line
        break
  return target
  

def ensureTFile(filename,option='READ',verb=0):
  """Open TFile, checking if the file in the given path exists."""
  if isinstance(filename,str):
    if ':' not in filename and not os.path.isfile(filename):
      LOG.throw(IOError,'File in path "%s" does not exist!'%(filename))
      exit(1)
    file = ROOT.TFile.Open(filename,option)
    if not file or file.IsZombie():
      LOG.throw(IOError,'Could not open file by name %r!'%(filename))
    LOG.verb("Opened file %s..."%(filename),verb,1)
  else:
    file = filename
    if not file or (hasattr(file,'IsZombie') and file.IsZombie()):
      LOG.throw(IOError,'Could not open file %r!'%(file))
  return file
  

def ensureTDirectory(file,dirname,cd=True,verb=0):
  """Make TDirectory in a file (or other TDirectory) if it does not yet exist."""
  directory = file.GetDirectory(dirname)
  if not directory:
    directory = file.mkdir(dirname)
    if verb>=1:
      print ">>> created directory %s in %s"%(dirname,file.GetName())
  if cd:
    directory.cd()
  return directory
  

def ensureinit(*paths,**kwargs):
  """Ensure an __init__.py exists, other wise, create one."""
  init   = os.path.join(os.path.join(*paths),'__init__.py')
  script = kwargs.get('by',"")
  if not os.path.isfile(init):
    print ">>> Creating '%s' to allow import of module..."%(init)
    with open(init,'w') as file:
      if script:
        script = "by "+script
      file.write("# Generated%s to allow import of the sample list modules\n"%(script))
  

def gethist(file,histname,setdir=True,close=None,retfile=False,fatal=True):
  """Get histogram from a given file."""
  if isinstance(file,str): # open TFile
    file = ensureTFile(file)
    if close==None:
      close = not retfile
  if not file or file.IsZombie():
    LOG.throw(IOError,'Could not open file by name "%s"'%(filename))
  hist = file.Get(histname)
  if not hist:
    if fatal:
      LOG.throw(IOError,'Did not find histogram %r in file %s!'%(histname,file.GetName()))
    else:
      LOG.warning('Did not find histogram %r in file %s!'%(histname,file.GetName()))
  if (close or setdir) and isinstance(hist,ROOT.TH1):
    hist.SetDirectory(0)
  if close: # close TFile
    file.Close()
  if retfile:
    return file, hist
  return hist
  
