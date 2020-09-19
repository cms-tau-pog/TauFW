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
    self.cutflow           = TH1D('cutflow','cutflow',25,0,25)
    self.cut_none          = 0
    self.cut_trig          = 1
    self.cut_muon          = 2
    self.cut_muon_veto     = 3
    self.cut_tau           = 4
    self.cut_electron_veto = 5
    self.cut_pair          = 6
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_none,           "no cut"        )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_trig,           "trigger"       )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_muon,           "muon"          )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_muon_veto,      "muon     veto" )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_tau,            "tau"           )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_electron_veto,  "electron veto" )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_pair,           "pair"          )
    
    # TREE
    self.tree        = TTree('tree','tree')
    self.pt_1        = np.zeros(1,dtype='f')
    self.eta_1       = np.zeros(1,dtype='f')
    self.q_1         = np.zeros(1,dtype='i')
    self.id_1        = np.zeros(1,dtype='?')
    self.iso_1       = np.zeros(1,dtype='f')
    self.genmatch_1  = np.zeros(1,dtype='f')
    self.decayMode_1 = np.zeros(1,dtype='i')
    self.pt_2        = np.zeros(1,dtype='f')
    self.eta_2       = np.zeros(1,dtype='f')
    self.q_2         = np.zeros(1,dtype='i')
    self.id_2        = np.zeros(1,dtype='i')
    self.iso_2       = np.zeros(1,dtype='f')
    self.genmatch_2  = np.zeros(1,dtype='f')
    self.decayMode_2 = np.zeros(1,dtype='i')
    self.m_vis       = np.zeros(1,dtype='f')
    self.tree.Branch('pt_1',         self.pt_1,        'pt_1/F'       )
    self.tree.Branch('eta_1',        self.eta_1,       'eta_1/F'      )
    self.tree.Branch('q_1',          self.q_1,         'q_1/I'        )
    self.tree.Branch('id_1',         self.id_1,        'id_1/O'       )
    self.tree.Branch('iso_1',        self.iso_1,       'iso_1/F'      )
    self.tree.Branch('genmatch_1',   self.genmatch_1,  'genmatch_1/F' )
    self.tree.Branch('decayMode_1',  self.decayMode_1, 'decayMode_1/I')
    self.tree.Branch('pt_2',         self.pt_2,  'pt_2/F'             )
    self.tree.Branch('eta_2',        self.eta_2, 'eta_2/F'            )
    self.tree.Branch('q_2',          self.q_2,   'q_2/I'              )
    self.tree.Branch('id_2',         self.id_2,  'id_2/I'             )
    self.tree.Branch('iso_2',        self.iso_2, 'iso_2/F'            )
    self.tree.Branch('genmatch_2',   self.genmatch_2,  'genmatch_2/F' )
    self.tree.Branch('decayMode_2',  self.decayMode_2, 'decayMode_2/I')
    self.tree.Branch('m_vis',        self.m_vis, 'm_vis/F'            )
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    
    # NO CUT
    self.cutflow.Fill(self.cut_none)
    
    # TRIGGER
    if not event.HLT_IsoMu27: return False
    self.cutflow.Fill(self.cut_trig)
    
    # SELECT MUON
    muons = [ ]
    # TODO: extend with a veto of additional muons. Veto muons should have the same quality selection as signal muons (or even looser),
    # but with a lower pt cut, e.g. muon.pt > 15.0
    veto_muons = [ ]

    for muon in Collection(event,'Muon'):
      good_muon = muon.mediumId and muon.pfRelIso04_all < 0.5 and abs(muon.eta) < 2.5
      signal_muon = good_muon and muon.pt > 28.0
      veto_muon   = False # TODO introduce a veto muon selection here
      if signal_muon:
        muons.append(muon)
      if veto_muon: # CAUTION: that's NOT an elif here!
        veto_muons.append(muon)
     
    if len(muons) == 0: return False
    self.cutflow.Fill(self.cut_muon)
    # TODO: What should be the requirement to veto events with additional muons?
    self.cutflow.Fill(self.cut_muon_veto)
    
    # SELECT TAU
    # TODO: Which decay modes of a tau should be considerd for an analysis? Extend tau selection accordingly
    taus = [ ]
    for tau in Collection(event,'Tau'):
      good_tau = tau.pt > 18.0 and tau.idDeepTau2017v2p1VSe >= 1 and tau.idDeepTau2017v2p1VSmu >= 1 and tau.idDeepTau2017v2p1VSjet >= 1
      if good_tau:
        taus.append(tau)
    if len(taus)<1: return False
    self.cutflow.Fill(self.cut_tau)

    # SELECT ELECTRONS FOR VETO
    # TODO: extend the selection of veto electrons: pt > 15.0, with loose WP of the mva based ID (Fall17 training) including isolation.
    electrons = []
    for electron in Collection(event,'Electron'):
      veto_electron = False # TODO introduce a veto electron selection here
      if veto_electron:
        electrons.append(electron)
    if len(electrons) > 1: return False
    self.cutflow.Fill(self.cut_electron_veto)
    
    # PAIR
    # TODO (optional): the mutau pair is constructed from a muon with highest pt and a tau with highest pt.
    # However, there is also the possibility to select the mutau pair according to the isolation.
    # If you like, you could try to implement mutau pair building algorithm, following the instructions on
    # https://twiki.cern.ch/twiki/bin/view/CMS/HiggsToTauTauWorking2017#Pair_Selection_Algorithm, but using the latest isolation quantities/discriminators
    muon = max(muons,key=lambda p: p.pt)
    tau  = max(taus,key=lambda p: p.pt)
    if muon.DeltaR(tau)<0.4: return False
    self.cutflow.Fill(self.cut_pair)
    
    # SAVE VARIABLES
    self.pt_1[0]        = muon.pt
    self.eta_1[0]       = muon.eta
    self.q_1[0]         = muon.charge
    self.id_1[0]        = muon.mediumId
    self.iso_1[0]       = muon.pfRelIso04_all # keep in mind: the SMALLER the value, the more the muon is isolated
    self.genmatch_1[0]  = muon.genPartFlav
    self.decayMode_1[0] = -1.0 # not needed for a muon
    self.pt_2[0]        = tau.pt
    self.eta_2[0]       = tau.eta
    self.q_2[0]         = tau.charge
    self.id_2[0]        = tau.idDeepTau2017v2p1VSjet
    self.iso_2[0]       = tau.rawDeepTau2017v2p1VSjet # keep in mind: the HIGHER the value of the discriminator, the more the tau is isolated
    self.genmatch_2[0]  = tau.genPartFlav
    self.decayMode_2[0] = tau.decayMode
    self.m_vis[0]       = (muon.p4()+tau.p4()).M()
    self.tree.Fill()
    
    return True
