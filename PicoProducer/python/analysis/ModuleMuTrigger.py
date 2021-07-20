# Author: Izaak Neutelings (July 2021)
# Description: Study muon triggers overlap via nanoAOD
# Instructions:
#   pico.py channel mutrig ModuleMuTrigger
#   pico.py run -c mutrig -y UL2016_preVFP UL2016_postVFP -s SingleMuon DYJ*M-50 -m 10000
#   pico.py submit -c mutrig -y UL2016_preVFP UL2016_postVFP --maxevts -1 --filesperjob 2 --queue short --time '0:50:00' -s SingleMuon DYJ*M-50
import sys
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.analysis.TreeProducer import *
from TauFW.PicoProducer.analysis.utils import ensurebranches
from TauFW.PicoProducer.corrections.MuonSFs import *


class ModuleMuTrigger(Module):
  
  def __init__(self, fname, **kwargs):
    self.year = kwargs.get('year', 2017   ) # integer, e.g. 2017, 2018
    self.era  = kwargs.get('era',  '2017' ) # string, e.g. '2017', 'UL2017'
    self.out  = TreeProducer(fname,self)
    if self.year==2016:
      self.trig1       = "IsoMu22"
      self.trig2       = "IsoMu24"
      self.trigger1    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      self.trigger2    = lambda e: e.HLT_IsoMu24 or e.IsoTkMu24
      self.muonCutPt1  = lambda e: 24
      self.muonCutPt1  = lambda e: 26
      self.muonCutEta1 = lambda e: 2.4 if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
      self.muonCutEta2 = lambda e: 2.4
    else:
      self.trig1       = "IsoMu24"
      self.trig2       = "IsoMu27"
      self.trigger1    = lambda e: e.HLT_IsoMu24
      self.trigger2    = lambda e: e.HLT_IsoMu27
      self.muon1CutPt1 = lambda e: 26
      self.muon1CutPt2 = lambda e: 29
      self.muonCutEta1 = lambda e: 2.4
      self.muonCutEta2 = lambda e: 2.4
    
    # TREE
    self.out.addBranch(self.trig1,   '?')
    self.out.addBranch(self.trig2,   '?')
    self.out.addBranch('trigsf',     'f')
    self.out.addBranch('pt_1',       'f')
    self.out.addBranch('eta_1',      'f')
    self.out.addBranch('iso_1',      'f')
    self.out.addBranch('idMedium_1', '?')
    self.out.addBranch('idTight_1',  '?')
    
    # CUTFLOW
    self.out.cutflow.addcut('none',        "no cut"                            )
    self.out.cutflow.addcut('trig1+trig1', "%s || %s"%(self.trig1,self.trig2)  ) # inclusive
    self.out.cutflow.addcut('trig1',       self.trig1                          )
    self.out.cutflow.addcut('trig2',       self.trig2                          )
    self.out.cutflow.addcut('trig1*trig2', "%s && %s"%(self.trig1,self.trig2)  )
    self.out.cutflow.addcut('trig1/trig2', "%s && !%s"%(self.trig1,self.trig2) )
    self.out.cutflow.addcut('trig2/trig1', "%s && !%s"%(self.trig2,self.trig1) )
    self.out.cutflow.addcut('muon',        "muon"                              )
  
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    """Before processing a new file."""
    sys.stdout.flush()
    if self.year==2016:
      branches = [
        ('HLT_IsoMu22_eta2p1',   False ),
        ('HLT_IsoTkMu22_eta2p1', False ),
        ('IsoMu24',              False ),
        ('IsoTkMu24',            False ),
      ]
      ensurebranches(inputTree,branches)
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    self.out.cutflow.fill('none')
    if not (self.trigger1(event) or self.trigger2(event)):
      return False
    
    # TRIGGER
    self.out.cutflow.fill('trig1+trig1') # inclusive
    if self.trigger1(event):
      self.out.cutflow.fill('trig1')
      if self.trigger2(event):
        self.out.cutflow.fill('trig1*trig2') # trig2 && trig1
      else:
        self.out.cutflow.fill('trig1/trig2') # trig1 && !trig2
    if self.trigger2(event):
      self.out.cutflow.fill('trig2')
      if not self.trigger1(event):
        self.out.cutflow.fill('trig2/trig1') # trig2 && !trig1
    
    # MUON
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<24: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.50: continue
      muons.append(muon)
    
    # FILL BRANCHES
    getattr(self.out,self.trig1)[0] = self.trigger1(event)
    getattr(self.out,self.trig2)[0] = self.trigger2(event)
    self.out.trigsf[0]              = 1.0 # TODO
    if len(muons)>0:
      self.out.cutflow.fill('muon')
      muon = muons[0]
      self.out.pt_1[0]       = muon.pt
      self.out.eta_1[0]      = muon.eta
      self.out.iso_1[0]      = muon.pfRelIso04_all # relative isolation
      self.out.idMedium_1[0] = muon.mediumId
      self.out.idTight_1[0]  = muon.tightId
    else:
      self.out.pt_1[0]       = -1.
      self.out.eta_1[0]      = -9.
      self.out.iso_1[0]      = -1.
      self.out.idMedium_1[0] = False
      self.out.idTight_1[0]  = False
    
    self.out.fill()
    return True
    
