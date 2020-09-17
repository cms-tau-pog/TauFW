# Author: Izaak Neutelings (May 2020)
# Description: Simple module to pre-select mutau events
from ROOT import TFile, TTree, TH1D
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class ModuleMuTau(Module):
  
  def __init__(self,fname,**kwargs):
    self.outfile = TFile(fname,'RECREATE')
  
  def beginJob(self):
    """Prepare output analysis tree and cutflow histogram."""
    
    # CUTFLOW HISTOGRAM
    self.cutflow  = TH1D('cutflow','cutflow',25,0,25)
    self.cut_none = 0
    self.cut_trig = 1
    self.cut_muon = 2
    self.cut_tau  = 3
    self.cut_pair = 4
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_none, "no cut"  )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_trig, "trigger" )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_muon, "muon"    )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_tau,  "tau"     )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_pair, "pair"    )
    
    # TREE
    self.tree   = TTree('tree','tree')
    self.pt_1   = np.zeros(1,dtype='f')
    self.eta_1  = np.zeros(1,dtype='f')
    self.q_1    = np.zeros(1,dtype='i')
    self.id_1   = np.zeros(1,dtype='?')
    self.iso_1  = np.zeros(1,dtype='f')
    self.pt_2   = np.zeros(1,dtype='f')
    self.eta_2  = np.zeros(1,dtype='f')
    self.q_2    = np.zeros(1,dtype='i')
    self.id_2   = np.zeros(1,dtype='i')
    self.iso_2  = np.zeros(1,dtype='f')
    self.m_vis  = np.zeros(1,dtype='f')
    self.tree.Branch('pt_1',   self.pt_1,  'pt_1/F' )
    self.tree.Branch('eta_1',  self.eta_1, 'eta_1/F')
    self.tree.Branch('q_1',    self.q_1,   'q_1/I'  )
    self.tree.Branch('id_1',   self.id_1,  'id_1/O' )
    self.tree.Branch('iso_1',  self.iso_1, 'iso_1/F')
    self.tree.Branch('pt_2',   self.pt_2,  'pt_2/F' )
    self.tree.Branch('eta_2',  self.eta_2, 'eta_2/F')
    self.tree.Branch('q_2',    self.q_2,   'q_2/I'  )
    self.tree.Branch('id_2',   self.id_2,  'id_2/I' )
    self.tree.Branch('iso_2',  self.iso_2, 'iso_2/F')
    self.tree.Branch('m_vis',  self.m_vis, 'm_vis/F')
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    
    # NO CUT
    self.cutflow.Fill(self.cut_none)
    
    # TRIGGER
    if not event.HLT_IsoMu24: return False
    self.cutflow.Fill(self.cut_trig)
    
    # SELECT MUON
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<20: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.50: continue
      muons.append(muon)
    if len(muons)<1: return False
    self.cutflow.Fill(self.cut_muon)
    
    # SELECT TAU
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if tau.pt<20: continue
      if abs(tau.eta)>2.4: continue
      if abs(tau.dz)>0.2: continue
      if tau.idDeepTau2017v2p1VSe<8: continue
      if tau.idDeepTau2017v2p1VSmu<1: continue
      if tau.idDeepTau2017v2p1VSjet<8: continue
      taus.append(tau)
    if len(taus)<1: return False
    self.cutflow.Fill(self.cut_tau)
    
    # PAIR
    muon = max(muons,key=lambda p: p.pt)
    tau  = max(taus,key=lambda p: p.pt)
    if muon.DeltaR(tau)<0.4: return False
    self.cutflow.Fill(self.cut_pair)
    
    # SAVE VARIABLES
    self.pt_1[0]   = muon.pt
    self.eta_1[0]  = muon.eta
    self.q_1[0]    = muon.charge
    self.id_1[0]   = muon.mediumId
    self.iso_1[0]  = muon.pfRelIso04_all
    self.pt_2[0]   = tau.pt
    self.eta_2[0]  = tau.eta
    self.q_2[0]    = tau.charge
    self.id_2[0]   = tau.idDeepTau2017v2p1VSjet
    self.iso_2[0]  = tau.rawIso
    self.m_vis[0]  = (muon.p4()+tau.p4()).M()
    self.tree.Fill()
    
    return True
