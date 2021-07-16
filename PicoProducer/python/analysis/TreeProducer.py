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
    self.filename = filename
    self.module   = module
    self.outfile  = TFile(filename,'RECREATE')
    ncuts         = kwargs.get('ncuts',25)
    self.cutflow  = Cutflow('cutflow',ncuts)
    self.display  = kwargs.get('display_cutflow',True)
    self.pileup   = TH1D('pileup', 'pileup', 100, 0, 100)
    self.tree     = TTree('tree','tree')
  
  def addBranch(self, name, dtype='f', default=None, title=None, arrname=None):
    """Add branch with a given name, and create an array of the same name as address."""
    if hasattr(self,name):
      raise IOError("Branch of name '%s' already exists!"%(name))
    if not arrname:
      arrname = name
    if isinstance(dtype,str): # Set correct data type for numpy:
      if dtype=='F':          # 'F' = 'complex64', which do not work for filling float branches
        dtype = 'float32'     # 'f' = 'float32' -> 'F' -> Float_t
    if isinstance(dtype,str): # Set correct data type for numpy:
      if dtype=='D':          # 'D' = 'complex128', which do not work for filling float branches
        dtype = 'float64'     # 'd' = 'float64' -> 'D' -> Double_t
    setattr(self,arrname,np.zeros(1,dtype=dtype))
    branch = self.tree.Branch(name,getattr(self,arrname),'%s/%s'%(name,root_dtype[dtype]))
    if default!=None:
      getattr(self,name)[0] = default
    if title:
      branch.SetTitle(title)
    return branch
  
  def fill(self):
    """Fill tree."""
    return self.tree.Fill()
  
  def endJob(self):
    """Write and close files after the job ends."""
    if self.display:
      self.cutflow.display()
      print ">>> Write %s..."%(self.outfile.GetName())
    self.outfile.Write()
    self.outfile.Close()
  
