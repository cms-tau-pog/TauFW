# Author: Izaak Neutelings (July 2022)
# Description: Keep track of number of events and sum of weights before and after skimming
from __future__ import print_function # for python3 compatibility
import time
import ROOT
from ROOT import TH1D
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


def printCutflow(cutflow):
  """Print rows of TH1 cutflow."""
  titles = {
    'full': "all events in the input tree",
    'read': "read events (after firstEntry, maxEvents)",
    'skim': "pre-skimmed events (after pre-selection cut, JSON)",
    'pass': "passed events (after selections by analysis modules)",
    'full_wgt': "all sum of weights in the input tree",
    'read_wgt': "read sum of weights",
    'skim_wgt': "pre-skimmed sum of weights",
    'pass_wgt': "passed events sum of weights",
  }
  den1 = cutflow.GetBinContent(1)
  den2 = cutflow.GetBinContent(2)
  print(">>> %13s %8s %8s"%('events','/full','/read'))
  for i in range(1,cutflow.GetXaxis().GetNbins()+1):
    label = cutflow.GetXaxis().GetBinLabel(i)
    num   = cutflow.GetBinContent(i)
    den1  = num if i in [5] else den1
    den2  = num if i in [6] else den2
    frac1 = "" if den1==0 else "%.2f%%"%(100.0*num/den1)
    frac2 = "" if den2==0 or num>den2 else "%.2f%%"%(100.0*num/den2)
    if label:
      title = titles.get(label,label)
      print(">>> %13.1f %8s %8s  %s"%(num,frac1,frac2,title))
  

class Bookkeeper(Module):
  
  def __init__(self,verb=0):
    # TODO: add histogram with sum of PDF and scale weights before any selections
    self.verb = verb # verbosity level
    if self.verb>=3:
      print(">>> Bookkeeper.__init__")
    self.cutflow = TH1D('cutflow_tot','cutflow',12,0,12) # total cutflow (all files)
    self.cutflow.SetDirectory(0)
    self.bin_full = 1
    self.bin_read = 2
    self.bin_skim = 3
    self.bin_pass = 4
    self.bin_full_wgt = 5
    self.bin_read_wgt = 6
    self.bin_skim_wgt = 7
    self.bin_pass_wgt = 8
    self.cutflow.GetXaxis().SetBinLabel(self.bin_full,'full') # all events in input tree before any cuts
    self.cutflow.GetXaxis().SetBinLabel(self.bin_read,'read') # after firstEntry, maxEvents
    self.cutflow.GetXaxis().SetBinLabel(self.bin_skim,'skim') # after pre-skimming (pre-selection cut, JSON)
    self.cutflow.GetXaxis().SetBinLabel(self.bin_pass,'pass') # after final selections by modules
    self.cutflow.GetXaxis().SetBinLabel(self.bin_full_wgt,'full_wgt')
    self.cutflow.GetXaxis().SetBinLabel(self.bin_read_wgt,'read_wgt')
    self.cutflow.GetXaxis().SetBinLabel(self.bin_skim_wgt,'skim_wgt')
    self.cutflow.GetXaxis().SetBinLabel(self.bin_pass_wgt,'pass_wgt')
  
  ###def beginJob(self):
  ###  """Prepare output analysis tree and cutflow histogram."""
  ###  if self.verb>=2:
  ###    print(">>> Bookkeeper.beginJob")
  
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    """Before processing a new file."""
    if self.verb>=3:
      print(">>> Bookkeeper.beginFile: tree entries, input=%r, output=%r"%(
        inputTree.GetEntries(),wrappedOutputTree.tree().GetEntries()))
    assert not outputFile.Get('cutflow'), "Input file cannot have pre-exisitng cutflow histogram!"
    outputFile.cutflow = self.cutflow.Clone('cutflow') # create cutflow for this output file
    outputFile.cutflow.SetName('cutflow')
    outputFile.cutflow.Reset()
    outputFile.cutflow.SetDirectory(outputFile)
  
  def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    """After processing a file."""
    time0 = time.time()
    outputTree = wrappedOutputTree.tree()
    cutflow = outputFile.cutflow
    maxEntries = wrappedOutputTree.maxEntries
    firstEntry = wrappedOutputTree.firstEntry
    if not maxEntries or maxEntries<0:
      maxEntries = ROOT.TVirtualTreePlayer.kMaxEntries
    if not firstEntry or firstEntry<0:
      firstEntry = 0
    elist  = inputTree._entrylist
    nread  = min(inputTree.GetEntries()-firstEntry,maxEntries)
    nskim  = elist.GetN() if elist else nread #inputTree.GetEntries()
    if self.verb>=2:
      print(">>> Bookkeeper.endFile: tree entries, input=%r, output=%r, first=%r, max=%r, nread=%r, nskim=%r"%(
        inputTree.GetEntries(),outputTree.GetEntries(),firstEntry,maxEntries,nread,nskim))
    assert nread>=nskim, "Number of read entries (%s) should be the larger or equal to the number of skimmed entries (%s)..."%(nread,nskim)
    
    # UNWEIGHTED
    cutflow.SetBinContent(self.bin_full,cutflow.GetBinContent(self.bin_full)+inputTree.GetEntries())
    cutflow.SetBinContent(self.bin_read,cutflow.GetBinContent(self.bin_read)+nread)
    cutflow.SetBinContent(self.bin_skim,cutflow.GetBinContent(self.bin_skim)+nskim)
    cutflow.SetBinContent(self.bin_pass,cutflow.GetBinContent(self.bin_pass)+outputTree.GetEntries())
    
    # WEIGHTED
    if hasattr(inputTree,'genWeight'): # for (NLO) MC
      if self.verb>=2:
        print(">>> Bookkeeper.endFile: Getting sum of weights...")
      #cutflow.SetBinContent(self.bin_read_wgt,inputTree.GetEntries('genWeight')+cutflow.GetBinContent(self.bin_read_wgt))
      inputTree.Draw("%s >> +cutflow"%(self.bin_full_wgt-0.5),'genWeight','gOff')
      inputTree.Draw("%s >> +cutflow"%(self.bin_read_wgt-0.5),'genWeight','gOff',maxEntries,firstEntry)
      if elist: # entry list after pre-skimming (firstEntry, maxEntries, pre-selection, JSON)
        inputTree.SetEntryList(elist)
        inputTree.Draw("%s >> +cutflow"%(self.bin_skim_wgt-0.5),'genWeight','gOff')
      else: # no pre-selection or JSON
        cutflow.SetBinContent(self.bin_skim_wgt,cutflow.GetBinContent(self.bin_read_wgt)) # reuse read sum of weights 
    if hasattr(outputTree,'genWeight'):
      outputTree.Draw("%s >> +cutflow"%(self.bin_pass_wgt-0.5),'genWeight','gOff')
    
    # WRITE
    self.cutflow.Add(cutflow) # add to total cutflow for final report
    outputFile.cutflow.SetDirectory(outputFile)
    cutflow.Write('cutflow',TH1D.kOverwrite)
    if self.verb>=2:
      print(">>> Bookkeeper.endFile: Cutflow for this file:")
      printCutflow(cutflow)
      print(">>> Bookkeeper.endJob: Filling cutflow took %.2f seconds"%(time.time()-time0))
    if self.verb>=3:
      print(">>> Bookkeeper.endFile: Intermediate total cutflow:")
      printCutflow(cutflow)
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    if self.verb>=2:
      print(">>> Bookkeeper.endJob")
    if self.verb>=1:
      print(">>> Bookkeeper.endFile: Final total cutflow:")
      printCutflow(self.cutflow)
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes, return False otherwise."""
    return True # default super class returns None
  
