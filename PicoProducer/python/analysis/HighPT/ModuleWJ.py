# Author: Jacopo Malvaso, Alexei Raspereza (December 2022)
# Description: Module to pre-select W+jets events for FF measurement
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerWJ import *
from TauFW.PicoProducer.analysis.ModuleHighPT import *
from TauFW.PicoProducer.analysis.utils import idIso, matchtaujet 
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher

class ModuleWJ(ModuleHighPT):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'wjets'
    super(ModuleWJ,self).__init__(fname,**kwargs)
    self.out     = TreeProducerWJ(fname,self)
        
    # TRIGGERS
    #if self.year==2016:
      #self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoTkMu24
      #self.muon1CutPt = lambda e: 26
      #self.muonCutEta = lambda e: 2.4 #if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
      #elif self.year==2017:
     # self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
     #self.muon1CutPt = lambda e: 26 if e.HLT_IsoMu24 else 29
     #self.muonCutEta = lambda e: 2.4
     #else:
     #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1

    self.muonPtCut = 30
    self.muonEtaCut = 2.4
    self.tauPtCut = 100
    self.tauEtaCut = 2.3
    self.metCut = 20
    self.mtCut = 50
    self.dphiCut = 2.0

    # CORRECTIONS
    if self.ismc:
      self.muSFs   = MuonSFs(era=self.era)

    # TRIGGERS
    jsonfile = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger = TrigObjMatcher(jsonfile,trigger='SingleMuon',isdata=self.isdata)
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('met' ,         "met cut"                    )
    self.out.cutflow.addcut('mT'  ,         "mT cut"                     )
    self.out.cutflow.addcut('dphi',         "dphi cut"                   )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleWJ,self).beginJob()
    print(">>> %-12s = %s"%('muonPtCut', self.muonPtCut))    
    print(">>> %-12s = %s"%('muonEtaCut', self.muonEtaCut))
    print(">>> %-12s = %s"%('tauPtCut', self.tauPtCut))    
    print(">>> %-12s = %s"%('tauEtaCut', self.tauEtaCut))
    print(">>> %-12s = %s"%('metCut', self.metCut))
    print(">>> %-12s = %s"%('mtCut', self.mtCut))
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
    if not self.trigger.fired(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<self.muonPtCut: continue
      if abs(muon.eta)>self.muonEtaCut: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if not self.trigger.match(event,muon): continue
      if muon.pfRelIso04_all>0.3: continue
      muons.append(muon)
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    muon1 = max(muons,key=lambda p: p.pt)
    
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
    leptons = [ muon1, tau1 ]
    jets, ht_muons, met, met_vars = self.fillJetMETBranches(event,leptons,muon1)

    if met.Pt()<self.metCut:
      return False
    self.out.cutflow.fill('met')

    if self.out.mt_1[0]<self.mtCut:
      return False
    self.out.cutflow.fill('mT')

    wboson = met + muon1.p4()

    self.out.dphi[0] = abs(wboson.DeltaPhi(tau1.p4()));

    if self.out.dphi[0]<self.dphiCut:
      return False
    self.out.cutflow.fill('dphi')

    # VETOS
    self.out.extramuon_veto[0] = self.get_extramuon_veto(event,leptons) 
    self.out.extraelec_veto[0] = self.get_extraelec_veto(event,leptons) 
    self.out.extratau_veto[0]  = self.get_extratau_veto(event,leptons)    
    
    # EVENT
    self.fillEventBranches(event)
        
    # MUON 1
    self.out.pt_1[0]       = muon1.pt
    self.out.eta_1[0]      = muon1.eta
    self.out.phi_1[0]      = muon1.phi
    self.out.dxy_1[0]      = muon1.dxy
    self.out.dz_1[0]       = muon1.dz
    self.out.q_1[0]        = muon1.charge
    self.out.iso_1[0]      = muon1.pfRelIso04_all # relative isolation
    self.out.idMedium_1[0] = muon1.mediumId
    self.out.idTight_1[0]  = muon1.tightId
    self.out.idHighPt_1[0] = muon1.highPtId

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
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = muon1.genPartFlav
      self.out.genmatch_2[0] = tau1.genPartFlav
      self.out.jpt_genmatch_2[0] = jpt_genmatch

    # WEIGHTS
    self.out.weight[0] = 1.0 # for data
    if self.ismc:
      self.fillCommonCorrBraches(event)      
      # MUON WEIGHTS
      self.out.trigweight[0]    = self.muSFs.getTriggerSF(muon1.pt,muon1.eta) # muon trigger SF
      self.out.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon1.pt,muon1.eta) # muon Id/iso SF
      self.out.weight[0] = self.out.trigweight[0]*self.out.puweight[0]*self.out.genweight[0]*self.out.idisoweight_1[0]
      if self.dozpt:
        self.out.weight[0] *= self.out.zptweight[0]
      if self.dotoppt:
        self.out.weight[0] *= self.out.ttptweight[0]

    self.out.fill()
    return True
  
  
