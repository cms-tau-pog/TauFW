#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Base class to create and prepare a custom output file & tree for analysis modules
# Sources:
#   https://root.cern.ch/doc/master/classTTree.html#addcolumnoffundamentaltypes
#   https://numpy.org/devdocs/user/basics.types.html
#   ROOT      Branch  numpy
#   Bool_t    'O'     '?'/'bool'/bool       8-bit boolean
#   UChar_t   'b'     'b'/'byte'/'int8'     8-bit unsigned integer
#   Int_t     'I'     'i'/'int32'          32-bit (signed) integer
#   Long64_t  'L'     'l'/'int62'/long     64-bit (signed) integer
#   Float_t   'F'     'f'/'float32'        32-bit float
#   Double_t  'D'     'd'/'float64'/float  64-bit float
import numpy as np
from ROOT import TTree, TFile, TH1D
from TauFW.PicoProducer.analysis.utils import Cutflow

root_dtype = { # python/numpy -> root data type
  '?': 'O',  'bool':    'O',  bool:   'O', # Bool_t  
  'b': 'b',  'int8':    'b',  'byte': 'b', # UChar_t 
  'i': 'I',  'int32':   'I',               # Int_t   
  'l': 'L',  'int64':   'L',  int:    'L', # Long64_t
  'f': 'F',  'float32': 'F',               # Float_t 
  'd': 'D',  'float64': 'D',  float:  'D', # Double_t
}
np_dtype = { # ROOT -> numpy data type
  'b': 'b', 'O': '?', 'I': 'int32', 'L': 'int64',
  'F': 'float32', 'D': 'float64',
}


class TreeProducer(object):
  """Base class to create and prepare a custom output file & tree for analysis modules."""
  
  def __init__(self, filename, module, **kwargs):
    self.verbosity = kwargs.get('verb',getattr(module,'verbosity',False) or getattr(module,'verb',False))
    if self.verbosity>=1:
      print ">>> TreeProducer.__init__: %r, %r, kwargs=%s..."%(filename,module,kwargs)
    self.filename  = filename
    self.module    = module
    self.outfile   = TFile(filename,'RECREATE')
    ncuts          = kwargs.get('ncuts',25)
    self.cutflow   = Cutflow('cutflow',ncuts) if ncuts>0 else None
    self.display   = kwargs.get('display',True) # display cutflow at the end
    self.pileup    = TH1D('pileup', 'pileup', 100, 0, 100)
    self.tree      = TTree('tree','tree')
    self.hists     = { } #OrderedDict() # extra histograms to be drawn
  
  def addHist(self,name,*args):
    """Add a histogram."""
    bins = args
    if len(args)==1 and isinstance(args[0],list): # list of binedges
      bins = np.array(args[0],'f')
      hist = TH1D(name,name,len(bins)-1,bins)
    elif len(args)==2 and isinstance(args[1],list): # title, list of binedges
      bins = np.array(args[1],'f')
      hist = TH1D(name,args[0],len(bins)-1,bins)
    elif len(args)==3: # nbins, xmin, xmax
      hist = TH1D(name,name,*args)
    elif len(args)==4: # title, nbins, xmin, xmax
      hist = TH1D(name,*args)
    else:
      raise IOError("TreeProducer.addHist: Could not parse histogram arguments: %r, args=%r"%(name,args))
    if self.verbosity>=1:
      print ">>> TreeProducer.addHist: Adding TH1D %r with bins %r..."%(name,bins)
    self.hists[name] = hist
    return hist
  
  def addBranch(self, name, dtype='f', default=None, title=None, arrname=None, **kwargs):
    """Add branch with a given name, and create an array of the same name as address."""
    if hasattr(self,name):
      raise IOError("Branch of name '%s' already exists!"%(name))
    if not arrname:
      arrname = name
    arrlen = kwargs.get('len',None) # make vector branch
    if arrlen: # vector branch
      if isinstance(arrlen,int): # integer: vector branch with fixed length
        maxlen = int(arrlen) # fixed length
      else: # string: vector branch with variable length, given by other branch
        maxlen = kwargs.get('max',120) # maximum length of address array
      arrstr = '['+str(arrlen)+']' # array length in leaf list
    else: # branch with single value
      maxlen = 1
      arrstr = ""
    if isinstance(dtype,str): # Set correct data type for numpy:
      if dtype=='F':          # 'F' = 'complex64', which do not work for filling float branches
        print ">>> TreeProducer.addBranch: Warning! Converting numpy data type 'F' (complex64) to 'f' (float32, Float_t)"
        dtype = 'float32'     # 'f' = 'float32' -> 'F' -> Float_t
      elif dtype=='D':        # 'D' = 'complex128', which do not work for filling float branches
        print ">>> TreeProducer.addBranch: Warning! Converting numpy data type 'D' (complex128) to 'd' (float64, Double_t)"
        dtype = 'float64'     # 'd' = 'float64' -> 'D' -> Double_t
    address = np.zeros(maxlen,dtype=dtype) # array address to be filled during event loop
    setattr(self,arrname,address)
    leaflist = "%s%s/%s"%(name,arrstr,root_dtype[dtype])
    if self.verbosity>=1:
      print ">>> TreeProducer.addBranch: tree.Branch(%r,%s,%r), %s=%r, maxlen=%s, default=%s"%(name,arrname,leaflist,arrname,address,maxlen,default)
    branch = self.tree.Branch(name,address,leaflist)
    if default!=None:
      if hasattr(default,'__getitem__'): # vector/array/list/tuple
        assert arrlen, "default=%r, but arrlen=%r for branch %r (dtype=%f)!"%(default,arrlen,name,dtype)
        assert len(default)<=len(address), "len(default)=%r > len(address)=%s for branch %r (dtype=%f)!"%(
                                            len(default),len(address),name,dtype)
        for i in range(len(default)):
          address[i] = default[i]
        if self.verbosity>=2:
          print ">>> TreeProducer.addBranch: Set default value %s to list %r: %r"%(arrname,default,address)
      else: # single value, like float or int
        for i in range(len(address)):
          address[i] = default
        if self.verbosity>=2:
          print ">>> TreeProducer.addBranch: Set default value %s to single value %r: %r"%(arrname,default,address)
    if title:
      branch.SetTitle(title)
    return branch
  
  def setAlias(self,newbranch,oldbranch):
    if self.verbosity>=1:
      print ">>> TreeProducer.setAlias: %r -> %r..."%(oldbranch,newbranch)
    self.tree.SetAlias(newbranch,oldbranch)
    return newbranch
  
  def fill(self,hname=None,*args):
    """Fill tree."""
    if hname: # fill histograms
      return self.hists[hname].Fill(*args)
    else: # fill trees
      return self.tree.Fill()
  
  def endJob(self):
    """Write and close files after the job ends."""
    if self.cutflow and self.display:
      self.cutflow.display()
      print ">>> Write %s..."%(self.outfile.GetName())
    self.outfile.Write()
    self.outfile.Close()
  
