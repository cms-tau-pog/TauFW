# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select munu events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerMuNu import *
from TauFW.PicoProducer.analysis.ModuleHighPT import *
from TauFW.PicoProducer.analysis.utils import idIso, matchtaujet 
from TauFW.PicoProducer.corrections.MuonSFs import *
#from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool


class ModuleMuNu(ModuleHighPT):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'munu'
    super(ModuleMuNu,self).__init__(fname,**kwargs)
    self.out     = TreeProducerMuNu(fname,self)
    
    
    # TRIGGERS
    if self.year==2016:
      #self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoTkMu24
      self.muon1CutPt = lambda e: 26
      self.muonCutEta = lambda e: 2.4 #if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
    elif self.year==2017:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = lambda e: 26 if e.HLT_IsoMu24 else 29
      self.muonCutEta = lambda e: 2.4
    else:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = lambda e: 26
      self.muonCutEta = lambda e: 2.4
    
    
    # CORRECTIONS
    if self.ismc:
      self.muSFs   = MuonSFs(era=self.era)
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('met' ,         "met"                        )
    self.out.cutflow.addcut('Wmass' ,       "mT cut"                     )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleMuNu,self).beginJob()
    print ">>> %-12s = %s"%('muon1CutPt', self.muon1CutPt)
    
    print ">>> %-12s = %s"%('muonCutEta', self.muonCutEta)
   
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
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<50: continue
      if abs(muon.eta)>self.muonCutEta(event): continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.5: continue
      muons.append(muon)
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    muon1 = max(muons,key=lambda p: p.pt)

        
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ ],[muon1],[ ],self.channel)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = extramuon_veto, extraelec_veto, dilepton_veto
    self.out.lepton_vetoes[0]       = extramuon_veto or extraelec_veto or dilepton_veto
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # MUON 1
    self.out.pt_1[0]       = muon1.pt
    self.out.eta_1[0]      = muon1.eta
    self.out.phi_1[0]      = muon1.phi
    self.out.m_1[0]        = muon1.mass
    self.out.y_1[0]        = muon1.p4().Rapidity()
    self.out.dxy_1[0]      = muon1.dxy
    self.out.dz_1[0]       = muon1.dz
    self.out.q_1[0]        = muon1.charge
    self.out.iso_1[0]      = muon1.pfRelIso04_all # relative isolation
    self.out.tkRelIso_1[0] = muon1.tkRelIso
    self.out.idMedium_1[0] = muon1.mediumId
    self.out.idTight_1[0]  = muon1.tightId
    self.out.idHighPt_1[0] = muon1.highPtId
    
    
    
    
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = muon1.genPartFlav
      
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,muon1) 
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBraches(event,jets,met,njets_vars,met_vars)
      if muon1.pfRelIso04_all<0.50 :
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # MUON WEIGHTS
      self.out.trigweight[0]    = self.muSFs.getTriggerSF(muon1.pt,muon1.eta) # assume leading muon was triggered on
      self.out.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon1.pt,muon1.eta)
      
    

    if met.Pt() < 50:
	return False
    self.out.cutflow.fill('met')


    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,muon1,met,met_vars) 
    
    


    self.out.fill()
    return True
    
