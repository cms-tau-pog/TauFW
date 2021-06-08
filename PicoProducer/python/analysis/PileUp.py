# Author: Izaak Neutelings (June 2021)
# Description: Simple module to compile pileup histograms in MC
# https://cms-nanoaod-integration.web.cern.ch/integration/cms-swmaster/mc106Xul16_doc.html#Pileup
# https://cms-nanoaod-integration.web.cern.ch/integration/cms-swmaster/mc106Xul16_doc.html#PV
from ROOT import TFile, TH1D, gDirectory
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class PileUp(Module):
  """Simple module to fill the pileup in a single histogram."""
  
  def __init__(self,fname,**kwargs):
    self.outfile = TFile(fname,'RECREATE')
    self.pileup = TH1D('pileup','pileup',100,0,100)
    self.npvs   = TH1D('PV_npvs','PV_npvs',100,0,100)
  
  #def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
  #  """Called when each file is opened."""
  #  hname  = 'pileup_tmp'
  #  pileup = self.pileup.Clone('pileup_tmp')
  #  pileup.Reset()
  #  inputTree.Draw("Pileup_nTrueInt >> pileup_tmp","","gOff") # faster C++ routine
  #  self.pileup.Add(pileup)
  #  gDirectory.Delete(hname)
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.pileup.Fill(event.Pileup_nTrueInt)
    self.npvs.Fill(event.PV_npvs)
    return False
  