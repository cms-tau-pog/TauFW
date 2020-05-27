#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Simple create mutau events
import numpy as np
from ROOT import TTree, TFile, TH1D, TH2D

root_dtype = {
  float: 'D',  int: 'I',  bool: 'O',
  'f':   'D',  'i': 'I',  '?':  'O',  'b': 'b',
}

np_dtype = {
  'D':   'f',  'I': 'i',  'O':  '?',  'b': 'b'
}


class TreeProducerCommon(object):
    """Class to create a custom output file & tree; as well as create and contain branches."""
    
    def __init__(self, filename, module, **kwargs):
        print 'TreeProducerCommon is called for', name
        
        ncuts         = kwargs.get('ncuts',25)
        self.filename = filename
        self.module   = module
        self.outfile  = TFile(filename,'RECREATE')
        self.tree     = TTree('tree','tree')
        self.cutflow  = TH1D('cutflow','cutflow',ncuts,0,ncuts)
    
    def addBranch(self, name, dtype='f', default=None, arrname=None):
        """Add branch with a given name, and create an array of the same name as address."""
        if hasattr(self,name):
          raise IOError("Branch of name '%s' already exists!"%(name))
        if not arrname:
          arrname = name
        if isinstance(dtype,str):
          if dtype.lower()=='f':   # 'f' is only a 'float32', and 'F' is a 'complex64', which do not work for filling float branches
            dtype = float          # float is a 'float64' ('f8')
          elif dtype.lower()=='i': # 'i' is only a 'int32'
            dtype = int            # int is a 'int64' ('i8')
        setattr(self,arrname,np.zeros(1,dtype=dtype))
        self.tree.Branch(name, getattr(self,arrname), '%s/%s'%(name,root_dtype[dtype]))
        if default!=None:
          getattr(self,name)[0] = default
    
    def endJob(self):
        """Write and close files after the job ends."""
        self.outfile.Write()
        self.outfile.Close()
    
