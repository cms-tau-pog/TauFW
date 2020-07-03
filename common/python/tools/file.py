# Author: Izaak Neutelings (May 2020)
import os, re, shutil
from abc import ABCMeta, abstractmethod
from subprocess import Popen, PIPE, STDOUT
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True


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
  

def ensureTFile(filename,option='READ'):
  """Open TFile, checking if the file in the given path exists."""
  if not os.path.isfile(filename):
    raise IOError('File in path "%s" does not exist!'%(filename))
    exit(1)
  file = ROOT.TFile(filename,option)
  if not file or file.IsZombie():
    raise IOError('Could not open file by name "%s"'%(filename))
    exit(1)
  return file
  

#def extractTH1(file,histname,setdir=True,close=None):
#  """Get histogram from a given file."""
#  if isinstance(file,str):
#    file = ensuretfile(file)
#    if close==None: close = True
#  if not file or file.IsZombie():
#    raise OSError('Could not open file!')
#    exit(1)
#  hist = file.Get(histname)
#  if not hist:
#    raise OSError('Did not find histogram "%s" in file %s!'%(histname,file.GetName()))
#    exit(1)
#  if (close or setdir) and isinstance(hist,TH1):
#    hist.SetDirectory(0)
#  if close:
#    file.Close()
#  return hist
#  
#
#def ensureTFileAndTH1(filename,histname,verbose=True,setdir=True):
#  """Open a TFile and get a histogram."""
#  if verbose:
#    print ">>>   %s"%(filename)
#  file = ensuretfile(filename,'READ')
#  hist = extractTH1(file,histname,setdir=setdir)
#  return file, hist

