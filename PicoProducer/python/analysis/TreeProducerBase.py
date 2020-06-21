#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Base class to create and prepare a custom output file & tree for analysis modules
import numpy as np
from ROOT import TTree, TFile
from TauFW.PicoProducer.analysis.utils import Cutflow

root_dtype = { # python/numpy -> root data type
  float: 'D',  int: 'I',  bool: 'O',
  'f':   'D',  'i': 'I',  '?':  'O',  'b': 'b',
}

np_dtype = { # ROOT -> numpy data type
  'D':   'f',  'I': 'i',  'O':  '?',  'b': 'b'
}


class TreeProducerBase(object):
  """Base class to create and prepare a custom output file & tree for analysis modules."""
  
  def __init__(self, filename, module, **kwargs):
    self.filename = filename
    self.module   = module
    self.outfile  = TFile(filename,'RECREATE')
    self.tree     = TTree('tree','tree')
    ncuts         = kwargs.get('ncuts',25)
    self.cutflow  = Cutflow('cutflow',ncuts)
  
  def addBranch(self, name, dtype='f', default=None, arrname=None):
    """Add branch with a given name, and create an array of the same name as address."""
    if hasattr(self,name):
      raise IOError("Branch of name '%s' already exists!"%(name))
    if not arrname:
      arrname = name
    if isinstance(dtype,str):  # Set correct data type for numpy:
      if dtype.lower()=='f':   # 'f' is only 'float32', and 'F'='complex64', which do not work for filling float branches
        dtype = float          # float='float64' ('f8')
      elif dtype.lower()=='i': # 'i' is only a 'int32'
        dtype = int            # int='int64' ('i8')
    setattr(self,arrname,np.zeros(1,dtype=dtype))
    self.tree.Branch(name,getattr(self,arrname),'%s/%s'%(name,root_dtype[dtype]))
    if default!=None:
      getattr(self,name)[0] = default
  
  def fill(self):
    """Fill tree."""
    return self.tree.Fill()
  
  def endJob(self):
    """Write and close files after the job ends."""
    self.outfile.Write()
    self.outfile.Close()
  

