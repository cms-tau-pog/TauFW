# Author: Izaak Neutelings (May 2020)
import os, re, shutil
from abc import ABCMeta, abstractmethod
from subprocess import Popen, PIPE, STDOUT
  

def writetemplate(templatename,outfilename,sublist=[],rmlist=[],**kwargs):
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
  

def ensuredir(*dirnames,**kwargs):
  """Make directory if it does not exist."""
  dirname   = os.path.join(*dirnames)
  empty     = kwargs.get('empty', False)
  verbosity = kwargs.get('verb',  0    )
  if not os.path.exists(dirname):
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
  """Ensure file exists."""
  fatal = kwargs.get('fatal',True)
  path = os.path.join(*paths)
  if not os.path.isfile(path):
    if fatal:
      raise IOError("Did not find file %s."%(path))
    else:
      print ">>> Warning! Did not find file %s."%(path)
  return path
  

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
  
