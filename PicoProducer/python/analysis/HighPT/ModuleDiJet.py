# Author: Jacopo Malvaso, Alexei Raspereza (December 2022)
# Description: Module to pre-select dijets events for FF measurement
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerDiJet import *
from TauFW.PicoProducer.analysis.ModuleHighPT import *
from TauFW.PicoProducer.analysis.utils import idIso, matchtaujet 
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher

class ModuleDiJet(ModuleHighPT):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'dijets'
    super(ModuleDiJet,self).__init__(fname,**kwargs)
    self.out     = TreeProducerDiJet(fname,self)
        
    # CUTS
    self.tauPtCut = 80
    self.tauEtaCut = 2.3
    self.dphiCut = 2.0

    # TRIGGERS
    self.trigger = lambda e: e.HLT_PFJet80 or e.HLT_PFJet140 or e.HLT_PFJet200 or e.HLT_PFJet260 or e.HLT_PFJet320 or e.HLT_PFJet400
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('njets',        "njets cut"                  )
    self.out.cutflow.addcut('dphi'  ,       "deltaphi cut"               )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleDiJet,self).beginJob()
    print(">>> %-12s = %s"%('tauPtCut', self.tauPtCut))    
    print(">>> %-12s = %s"%('tauEtaCut', self.tauEtaCut))
    print(">>> %-12s = %s"%('dphiCut', self.dphiCut))
   
    pass
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    if not self.fillhists(event):
      return False
    
    
    ##### TRIGGER ####################################
    if not self.trigger(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### TAU #######################################
    
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if tau.pt<self.tauPtCut: continue
      if abs(tau.eta)>self.tauEtaCut: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      if tau.idDeepTau2017v2p1VSe<1: continue # VVVLoose
      if tau.idDeepTau2017v2p1VSmu<1: continue # VLoose
      if tau.idDeepTau2017v2p1VSjet<1: continue # VVVLoose
      if tau.pt<self.tauPtCut: continue
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    tau1 = max(taus,key=lambda p: p.pt)

    # JETS
    leptons = [ tau1 ]
    jets, ht_muons, met, met_vars = self.fillJetMETBranches(event,leptons,tau1)
    if len(jets)==0:
      return False
    if self.out.njets>1:
      return False
    self.out.cutflow.fill('njets')

    jet = max(jets,key=lambda p: p.pt)

    self.out.dphi[0] = abs(jet.p4().DeltaPhi(tau1.p4()));
    
    if self.out.dphi[0]<self.dphiCut:
      return False
    self.out.cutflow.fill('dphi')

    # VETOS
    self.out.extramuon_veto[0] = self.get_extramuon_veto(event,leptons) 
    self.out.extraelec_veto[0] = self.get_extraelec_veto(event,leptons) 
    self.out.extratau_veto[0]  = self.get_extratau_veto(event,leptons)    
    
    # EVENT
    self.fillEventBranches(event)
        
    # TAU 2
    self.out.pt_2[0]                       = tau1.pt
    self.out.eta_2[0]                      = tau1.eta
    self.out.phi_2[0]                      = tau1.phi
    self.out.m_2[0]                        = tau1.mass
    self.out.q_2[0]                        = tau1.charge
    self.out.dm_2[0]                       = tau1.decayMode
    self.out.rawDeepTau2017v2p1VSe_2[0]    = tau1.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau1.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau1.rawDeepTau2017v2p1VSjet
    self.out.idDeepTau2017v2p1VSe_2[0]     = tau1.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_2[0]    = tau1.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_2[0]   = tau1.idDeepTau2017v2p1VSjet
    jpt_match, jpt_genmatch = matchtaujet(event,tau1,self.ismc)
    if jpt_match>10:
      self.out.jpt_match_2[0] = jpt_match
    else:
      self.out.jpt_match_2[0] = self.out.pt_2[0]
    self.out.jpt_ratio_2[0] = self.out.pt_2[0]/self.out.jpt_match_2[0]

    #######
    # JET #
    #######
    self.out.jpt[0] = jet.pt
    self.out.jeta[0] = jet.eta
    self.out.jphi[0] = jet.phi
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_2[0] = tau1.genPartFlav
      self.out.jpt_genmatch_2[0] = jpt_genmatch

    # WEIGHTS
    self.out.weight[0] = 1.0 # for data
    if self.ismc:
      self.fillCommonCorrBranches(event)      
      self.out.trigweight[0] = 1.0
      self.out.weight[0] = self.out.trigweight[0]*self.out.puweight[0]*self.out.genweight[0]*self.out.idisoweight_1[0]
      if self.dozpt:
        self.out.weight[0] *= self.out.zptweight[0]
      if self.dotoppt:
        self.out.weight[0] *= self.out.ttptweight[0]

    self.out.fill()
    return True
  
  
