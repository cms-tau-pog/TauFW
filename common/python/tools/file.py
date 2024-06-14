# Author: Izaak Neutelings (May 2020)
from __future__ import print_function # for python3 compatibility
from past.builtins import basestring # for python2 compatibility
import os, re, shutil, glob
import importlib, traceback
from TauFW.common.tools.log import LOG
from TauFW.common.tools.utils import ensurelist, isglob
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
  empty     = kwargs.get('empty', False )
  verbosity = kwargs.get('verb',  0     )
  if not dirname:
    return dirname
  elif '$' in dirname: # expand environmental variables
    dirname = os.path.expandvars(dirname)
  if not os.path.exists(dirname):
    if verbosity>=1:
      print(">>> Making directory %r..."%(dirname))
    os.makedirs(dirname)
    if not os.path.exists(dirname):
      print(">>> Failed to make directory %r"%(dirname))
  elif empty: # make sure directory is empty
    for filename in os.listdir(dirname): # remove all contents
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
      print(">>> Warning! Did not find file %s."%(path))
    #path = None
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
    traceback.format_exc()
    LOG.throw(ImportError,"Importing module '%s' failed. Please check %s! cwd=%r"%(modpath,modfile,os.getcwd()))
  if not hasattr(module,modclass):
    LOG.throw(IOError,"Module '%s' in %s does not have a module named '%s'!"%(module,modfile,modname))
  return module
  

def expandfiles(files,verb=0):
  """Expend glob patterns in file list."""
  files = files[:] # create new list
  for fname in files[:]:
    if isglob(fname):
      fnames = glob.glob(fname) # expand glob pattern
      if verb>=1:
        print(">>> expandfiles: %r -> %s"%(fname,fnames))
      index = files.index(fname)
      files = files[:index] + fnames + files[index+1:] # insert expanded list
  return files
  

def rmfile(filepaths,verb=0):
  """Remove (list of) files."""
  if isinstance(filepaths,basestring):
    filepaths = [filepaths]
  for filepath in filepaths[:]:
    if isglob(filepath):
      subpaths = glob.glob(filepath)
      i = filepaths.index(filepath)
      filepaths = filepaths[:i] + subpaths + filepaths[i+1:] # insert
  for filepath in filepaths:
    if os.path.isfile(filepath):
      if verb>=2:
        print(">>> rmfile: Removing %r..."%(filepath))
      os.unlink(filepath)
    elif verb>=2:
      print(">>> rmfile: Did not find %r..."%(filepath))
  

def getline(fname,iline):
  target = ""
  with open(fname) as file:
    for i, line in enumerate(file):
      if i==iline:
        target = line
        break
  return target
  

def ensureinit(*paths,**kwargs):
  """Check if an __init__.py exists. Create one if it does not exist."""
  init   = os.path.join(os.path.join(*paths),'__init__.py')
  script = kwargs.get('by',"")
  if not os.path.isfile(init):
    print(">>> Creating '%s' to allow import of module..."%(init))
    with open(init,'w') as file:
      if script:
        script = "by "+script
      file.write("# Generated%s to allow import of the sample list modules\n"%(script))
  
