# Author: Izaak Neutelings (July 2023)
from __future__ import print_function # for python3 compatibility
from past.builtins import basestring # for python2 compatibility
import os
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile
from TauFW.common.tools.log import LOG
from TauFW.common.tools.utils import unwraplistargs, islist


def rootname(*args):
  """Convert list of TNamed objects to list of names."""
  if len(args)==1 and not islist(args[0]):
    obj   = args[0]
    names = obj.GetName() if hasattr(obj,'GetName') else str(obj) # return string
  else:
    args = unwraplistargs(args)
    names = [getname(o) for o in args ] # return list of strings
  return names
  

def rootrepr(*args,**kwargs):
  """Create representation string for ROOT objects."""
  if len(args)==1 and not islist(args[0]):
    obj   = args[0]
    if hasattr(obj,'GetName') and hasattr(obj,'GetTitle'):
      if kwargs.get('id',False): # include hex id
        names = "<%s(%r,%r) at %s>"%(obj.__class__.__name__,obj.GetName(),obj.GetTitle(),hex(id(obj)))
      else:
        names = "%s(%r,%r)"%(obj.__class__.__name__,obj.GetName(),obj.GetTitle())
    else:
      names = repr(obj)
  else:
    args = unwraplistargs(args)
    names = [rootrepr(o) for o in args ] # return list of strings
    if kwargs.get('join',True):
      names = '['+', '.join(names)+']' # return string of list
  return names
  

def ensureTFile(filename,option='READ',compress=None,verb=0):
  """Open TFile, checking if the file in the given path exists."""
  if isinstance(filename,basestring):
    if option=='READ' and ':' not in filename and not os.path.isfile(filename):
      LOG.throw(IOError,'File in path "%s" does not exist!'%(filename))
      exit(1)
    if compress==None:
      file = ROOT.TFile.Open(filename,option,filename)
    else:
      compresslevel, compressalgo = parsecompression(compress)
      file = ROOT.TFile.Open(filename,option,filename,compresslevel)
      if compressalgo!=None:
        file.SetCompressionAlgorithm(compressalgo)
      LOG.verb("ensureTFile: Using compression algorithm %s with level %s"%(compressalgo,compresslevel),verb+2,1)
    if not file or file.IsZombie():
      LOG.throw(IOError,'Could not open file by name %r!'%(filename))
    LOG.verb("Opened file %s..."%(filename),verb,1)
  else:
    file = filename
    if not file or (hasattr(file,'IsZombie') and file.IsZombie()):
      LOG.throw(IOError,'Could not open file %r!'%(file))
  return file
  

def parsecompression(compression='LZMA:9'):
  # https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/postprocessor.py
  level = 0    # ROOT.RCompressionSetting.EDefaults.EValues.kUseCompiledDefault
  algo  = None # ROOT.RCompressionSetting.EAlgorithm.kUseGlobal
  if compression!=None:
    if isinstance(compression,int):
      level = compression
    elif isinstance(compression,str) and compression.isdigit():
      level = int(compression)
    elif isinstance(compression,str) and compression.count(':')==1:
      #ROOT.gInterpreter.ProcessLine("#include <Compression.h>")
      (algo, level) = compression.split(":")
      level = int(level)
      if 'LZMA' in algo:
        algo = ROOT.ROOT.kLZMA
      elif 'ZLIB' in algo:
        algo = ROOT.ROOT.kZLIB
      elif 'LZ4' in algo:
        algo = ROOT.ROOT.kLZ4
      else:
        raise RuntimeError("Unsupported compression %s"%algo)
    else:
      LOG.error("Compression setting must be a string of the form 'algo:level', e.g. 'LZMA:9'. "
                "Got %r"%(compression))
  return level, algo
  

def ensureTDirectory(file,dirname,cd=True,split=True,verb=0):
  """Make TDirectory in a file (or other TDirectory) if it does not yet exist."""
  if split and '/' in dirname: # split subdirectory structure to ensure they exist recursively
    dirs = dirname.strip('/').split('/')
    topdir = '/'.join(dirs[:-1])
    dirname = dirs[-1]
    file = ensureTDirectory(file,topdir,cd=False,verb=verb) # create top dirs recursively
  directory = file.GetDirectory(dirname)
  if not directory:
    directory = file.mkdir(dirname)
    if verb>=1:
      print(">>> Created directory %s in %s"%(dirname,file.GetPath()))
  if cd:
    directory.cd()
  return directory
  

def gethist(file,histname,setdir=True,close=None,retfile=False,fatal=True,warn=True):
  """Get histogram from a given file."""
  if isinstance(file,basestring): # open TFile
    file = ensureTFile(file)
    if close==None:
      close = not retfile
  if not file or file.IsZombie():
    LOG.throw(IOError,"Could not open file by name %r"%(filename))
  hist = file.Get(histname)
  if not hist:
    if fatal:
      LOG.throw(IOError,"Did not find histogram %r in file %r!"%(histname,file.GetPath()))
    elif warn:
      LOG.warn("Did not find histogram %r in file %r!"%(histname,file.GetPath()))
  if (close or setdir) and isinstance(hist,ROOT.TH1):
    hist.SetDirectory(0)
  if close: # close TFile
    file.Close()
  if retfile:
    return file, hist
  return hist
  
