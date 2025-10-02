# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select mumu events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerMuMu import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonPair, idIso, matchtaujet
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
#from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool


class ModuleMuMu(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mumu'
    super(ModuleMuMu,self).__init__(fname,**kwargs)
    self.out     = TreeProducerMuMu(fname,self)
    self.zwindow = kwargs.get('zwindow', False ) # stay between 70 and 110 GeV
    
    # TRIGGERS
    if self.year==2016:
      #self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoTkMu24
      self.muon1CutPt = lambda e: 26
      self.muonCutEta = lambda e: 2.4 #if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
    elif self.year==2017:
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = lambda e: 26 if e.HLT_IsoMu24 else 29
      self.muonCutEta = lambda e: 2.4
    elif self.year==2022:
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27#e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt  = lambda e: 26
      self.muonCutEta = lambda e: 2.4
    else:
      #self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muon1CutPt = lambda e: 26
      self.muonCutEta = lambda e: 2.4
    self.muon2CutPt   = 15
    self.tauCutPt     = 20
    self.tauCutEta    = 2.3
    
    # CORRECTIONS
    if self.ismc:
      self.muSFs   = MuonSFs(era=self.era)

    # TRIGGERS
    jsonfile = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(2018))
    self.trigger = TrigObjMatcher(jsonfile,trigger='SingleMuon',isdata=self.isdata)
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('jetvetoes',    "jet vetoes"                 )
    self.out.cutflow.addcut('leadTrig',     "leading muon triggered"     ) # ADDED FOR SF CROSS CHECKS!
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    self.out.cutflow.addcut('weight_mutaufilter', "no cut, mutaufilter", 17 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP0orp4', "no cut, weighted, mutau, 0 or >4 jets", 18 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP1', "no cut, weighted, mutau, 1 jet", 19 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP2', "no cut, weighted, mutau, 2 jets", 20 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP3', "no cut, weighted, mutau, 3 jets", 21 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP4', "no cut, weighted, mutau, 4 jets", 22 )
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleMuMu,self).beginJob()
    print(">>> %-12s = %s"%('muon1CutPt', self.muon1CutPt))
    print(">>> %-12s = %s"%('muon2CutPt', self.muon2CutPt))
    print(">>> %-12s = %s"%('muonCutEta', self.muonCutEta))
    print(">>> %-12s = %s"%('tauCutPt',   self.tauCutPt))
    print(">>> %-12s = %s"%('tauCutEta',  self.tauCutEta))
    print(">>> %-12s = %s"%('zwindow',    self.zwindow))
    print(">>> %-12s = %s"%('trigger',    self.trigger))
    pass
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    if not self.fillhists(event):
      return False
    
    
    ##### TRIGGER ####################################
    #if not self.trigger(event):
    if not self.trigger.fired(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<self.muon2CutPt: continue # lower pt cut
      if abs(muon.eta)>self.muonCutEta(event): continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.50: continue
      muons.append(muon)
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    
    
    ##### MUMU PAIR #################################
    dileps = [ ]
    ptcut  = self.muon1CutPt(event) # trigger dependent
    for i, muon1 in enumerate(muons,1):
      for muon2 in muons[i:]:
        if muon2.DeltaR(muon1)<0.5: continue
        if muon1.pt<ptcut and muon2.pt<ptcut: continue # larger pt cut
        if self.zwindow and not (70<(muon1.p4()+muon2.p4()).M()<110): continue # Z mass
        ltau = LeptonPair(muon1,muon1.pfRelIso04_all,muon2,muon2.pfRelIso04_all)
        dileps.append(ltau)
    if len(dileps)==0:
      return False
    muon1, muon2 = max(dileps).pair
    muon1.tlv    = muon1.p4()
    muon2.tlv    = muon2.p4()
    self.out.cutflow.fill('pair')

    if "202" in self.year:
        if self.jetveto(event): return False 
    self.out.cutflow.fill('jetvetoes')
    
    # ADDED FOR SF CROSS CHECKS!
    # Only keep events with leading muon triggered
    if not self.trigger.match(event,muon1): 
      return False
    self.out.cutflow.fill('leadTrig')
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ ],[muon1,muon2],[ ],self.channel, era=self.era)
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
    self.out.y_1[0]        = muon1.tlv.Rapidity()
    self.out.dxy_1[0]      = muon1.dxy
    self.out.dz_1[0]       = muon1.dz
    self.out.q_1[0]        = muon1.charge
    self.out.iso_1[0]      = muon1.pfRelIso04_all # relative isolation
    #self.out.tkRelIso_1[0] = muon1.tkRelIso
    self.out.idMedium_1[0] = muon1.mediumId
    self.out.idTight_1[0]  = muon1.tightId
    self.out.idHighPt_1[0] = muon1.highPtId
    
    
    # MUON 2
    self.out.pt_2[0]       = muon2.pt
    self.out.eta_2[0]      = muon2.eta
    self.out.phi_2[0]      = muon2.phi
    self.out.m_2[0]        = muon2.mass
    self.out.y_2[0]        = muon2.tlv.Rapidity()
    self.out.dxy_2[0]      = muon2.dxy
    self.out.dz_2[0]       = muon2.dz
    self.out.q_2[0]        = muon2.charge
    self.out.iso_2[0]      = muon2.pfRelIso04_all # relative isolation
    #self.out.tkRelIso_2[0] = muon2.tkRelIso
    self.out.idMedium_2[0] = muon2.mediumId
    self.out.idTight_2[0]  = muon2.tightId
    self.out.idHighPt_2[0] = muon2.highPtId
    
    
    # TAU for jet -> tau fake rate measurement in mumu+tau events
    maxtau = None
    ptmax  = 20
    for tau in Collection(event,'Tau'):
      if tau.pt<ptmax: continue
      if muon1.DeltaR(tau)<0.5: continue
      if muon2.DeltaR(tau)<0.5: continue
      if abs(tau.eta)>2.3: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      #if ord(tau.idDeepTau2017v2p1VSe)<1: continue # VLoose
      #if ord(tau.idDeepTau2017v2p1VSmu)<1: continue # VLoose
      maxtau = tau
      ptmax  = tau.pt
    if maxtau!=None:
      self.out.pt_3[0]                     = maxtau.pt
      self.out.eta_3[0]                    = maxtau.eta
      self.out.m_3[0]                      = maxtau.mass
      self.out.q_3[0]                      = maxtau.charge
      self.out.dm_3[0]                     = maxtau.decayMode
      self.out.iso_3[0]                    = maxtau.rawIso
      #self.out.idiso_2[0]                  = idIso(maxtau) # cut-based tau isolation (rawIso)
      #self.out.idAntiEle_3[0]              = maxtau.idAntiEle
      #self.out.idAntiMu_3[0]               = maxtau.idAntiMu
      #self.out.idMVAoldDM2017v2_3[0]       = maxtau.idMVAoldDM2017v2
      #self.out.idMVAnewDM2017v2_3[0]       = maxtau.idMVAnewDM2017v2
      self.out.idDeepTau2017v2p1VSe_3[0]   = maxtau.idDeepTau2017v2p1VSe
      self.out.idDeepTau2017v2p1VSmu_3[0]  = maxtau.idDeepTau2017v2p1VSmu
      self.out.idDeepTau2017v2p1VSjet_3[0] = maxtau.idDeepTau2017v2p1VSjet
      #self.out.idDeepTau2018v2p5VSe_3[0]   = maxtau.idDeepTau2018v2p5VSe
      #self.out.idDeepTau2018v2p5VSmu_3[0]  = maxtau.idDeepTau2018v2p5VSmu
      #self.out.idDeepTau2018v2p5VSjet_3[0] = maxtau.idDeepTau2018v2p5VSjet
      if self.ismc:
        self.out.jpt_match_3[0], self.out.jpt_genmatch_3[0] = matchtaujet(event,maxtau,self.ismc)
        self.out.genmatch_3[0]             = maxtau.genPartFlav
      else:
        self.out.jpt_match_3[0] = matchtaujet(event,maxtau,self.ismc)[0]
    else:
      self.out.pt_3[0]                     = -1
      self.out.eta_3[0]                    = -9
      self.out.m_3[0]                      = -1
      self.out.q_3[0]                      =  0
      self.out.dm_3[0]                     = -1
      #self.out.idAntiEle_3[0]              = -1
      #self.out.idAntiMu_3[0]               = -1
      #self.out.idMVAoldDM2017v2_3[0]       = -1
      #self.out.idMVAnewDM2017v2_3[0]       = -1
      self.out.idDeepTau2017v2p1VSe_3[0]   = -1
      self.out.idDeepTau2017v2p1VSmu_3[0]  = -1
      self.out.idDeepTau2017v2p1VSjet_3[0] = -1
      self.out.idDeepTau2018v2p5VSe_3[0]   = -1
      self.out.idDeepTau2018v2p5VSmu_3[0]  = -1
      self.out.idDeepTau2018v2p5VSjet_3[0] = -1
      self.out.iso_3[0]                    = -1
      self.out.jpt_match_3[0]              = -1
      if self.ismc:
        self.out.jpt_genmatch_3[0]         = -1
        self.out.genmatch_3[0]             = -1
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = muon1.genPartFlav
      self.out.genmatch_2[0] = muon2.genPartFlav
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,muon1,muon2)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if muon1.pfRelIso04_all<0.50 and muon2.pfRelIso04_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # MUON WEIGHTS
      self.out.trigweight[0]    = self.muSFs.getTriggerSF(muon1.pt,muon1.eta) # assume leading muon was triggered on
      self.out.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon1.pt,muon1.eta)
      self.out.idisoweight_2[0] = self.muSFs.getIdIsoSF(muon2.pt,muon2.eta)
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,muon1,muon2,met,met_vars)
    
    
    self.out.fill()
    return True
    
