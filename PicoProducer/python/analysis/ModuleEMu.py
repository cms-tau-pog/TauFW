# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select mumu events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerEMu import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonPair, idIso, matchtaujet
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.ElectronSFs import *
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool


class ModuleEMu(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'emu'
    super(ModuleEMu,self).__init__(fname,**kwargs)
    self.out = TreeProducerEMu(fname,self)
    
    # TRIGGERS
    if self.year==2016:
      self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      self.muonCutPt  = lambda e: 23
      self.muonCutEta = lambda e: 2.4 if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
    elif self.year==2017:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muonCutPt  = lambda e: 25 if e.HLT_IsoMu24 else 28
      self.muonCutEta = lambda e: 2.4
    else:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muonCutPt  = lambda e: 25
      self.muonCutEta = lambda e: 2.4
    self.eleCutPt     = 15
    self.eleCutEta    = 2.3
    self.tauCutPt     = 20
    self.tauCutEta    = 2.3
    
    # CORRECTIONS
    if self.ismc:
      self.muSFs   = MuonSFs(era=self.era)
      self.eleSFs  = ElectronSFs(era=self.era)
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('electron',     "electron"                   )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleEMu,self).beginJob()
    print ">>> %-12s = %s"%('muonCutPt',  self.muonCutPt)
    print ">>> %-12s = %s"%('muonCutEta', self.muonCutEta)
    print ">>> %-12s = %s"%('eleCutPt',   self.eleCutPt)
    print ">>> %-12s = %s"%('eleCutEta',  self.eleCutEta)
    print ">>> %-12s = %s"%('tauCutPt',   self.tauCutPt)
    print ">>> %-12s = %s"%('tauCutEta',  self.tauCutEta)
    pass
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    self.out.cutflow.fill('none')
    if self.isdata:
      self.out.cutflow.fill('weight',1.)
      if event.PV_npvs>0:
        self.out.cutflow.fill('weight_no0PU',1.)
      else:
        return False
    else:
      self.out.cutflow.fill('weight',event.genWeight)
      self.out.pileup.Fill(event.Pileup_nTrueInt)
      if event.Pileup_nTrueInt>0:
        self.out.cutflow.fill('weight_no0PU',event.genWeight)
      else:
        return False
    
    
    ##### TRIGGER ####################################
    if not self.trigger(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### ELECTRON ###################################
    electrons = [ ]
    for electron in Collection(event,'Electron'):
      #if self.ismc and self.ees!=1:
      #  electron.pt   *= self.ees
      #  electron.mass *= self.ees
      if electron.pt<self.eleCutPt: continue
      if abs(electron.eta)>self.eleCutEta: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if not electron.convVeto: continue
      if electron.lostHits>1: continue
      if not (electron.mvaFall17V2Iso_WP90 or electron.mvaFall17V2noIso_WP90): continue
      electrons.append(electron)
    if len(electrons)==0:
      return False
    self.out.cutflow.fill('electron')
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<self.muonCutPt(event): continue
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
    for electron in electrons:
      for muon in muons:
        if muon.DeltaR(electron)<0.5: continue
        ltau = LeptonPair(electron,electron.pfRelIso03_all,muon,muon.pfRelIso04_all)
        dileps.append(ltau)
    if len(dileps)==0:
      return False
    electron, muon = max(dileps).pair
    electron.tlv   = electron.p4()
    muon.tlv       = muon.p4()
    self.out.cutflow.fill('pair')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[electron],[muon],[ ],self.channel)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[electron],[muon],[ ],self.channel)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # MUON 1
    self.out.pt_1[0]                  = electron.pt
    self.out.eta_1[0]                 = electron.eta
    self.out.phi_1[0]                 = electron.phi
    self.out.m_1[0]                   = electron.mass
    self.out.y_1[0]                   = electron.tlv.Rapidity()
    self.out.dxy_1[0]                 = electron.dxy
    self.out.dz_1[0]                  = electron.dz
    self.out.q_1[0]                   = electron.charge
    self.out.iso_1[0]                 = electron.pfRelIso03_all
    self.out.cutBased_1[0]            = electron.cutBased
    self.out.mvaFall17Iso_WP90_1[0]   = electron.mvaFall17V2Iso_WP90
    self.out.mvaFall17Iso_WP80_1[0]   = electron.mvaFall17V2Iso_WP80
    self.out.mvaFall17noIso_WP90_1[0] = electron.mvaFall17V2noIso_WP90
    self.out.mvaFall17noIso_WP80_1[0] = electron.mvaFall17V2noIso_WP80
    
    
    # MUON 2
    self.out.pt_2[0]  = muon.pt
    self.out.eta_2[0] = muon.eta
    self.out.phi_2[0] = muon.phi
    self.out.m_2[0]   = muon.mass
    self.out.y_2[0]   = muon.tlv.Rapidity()
    self.out.dxy_2[0] = muon.dxy
    self.out.dz_2[0]  = muon.dz
    self.out.q_2[0]   = muon.charge
    self.out.iso_2[0] = muon.pfRelIso04_all
    
    
    # TAU for jet -> tau fake rate measurement in emu+tau events
    maxtau = None
    ptmax  = 20
    for tau in Collection(event,'Tau'):
      if tau.pt<ptmax: continue
      if electron.DeltaR(tau)<0.5: continue
      if muon.DeltaR(tau)<0.5: continue
      if abs(tau.eta)>2.3: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      #if ord(tau.idDeepTau2017v2p1VSe)<1: continue # VLoose
      #if ord(tau.idDeepTau2017v2p1VSmu)<1: continue # VLoose
      maxtau = tau
      ptmax  = tau.pt
    if maxtau>-1:
      self.out.pt_3[0]                     = maxtau.pt
      self.out.eta_3[0]                    = maxtau.eta
      self.out.m_3[0]                      = maxtau.mass
      self.out.q_3[0]                      = maxtau.charge
      self.out.dm_3[0]                     = maxtau.decayMode
      self.out.iso_3[0]                    = maxtau.rawIso
      self.out.idiso_2[0]                  = idIso(maxtau) # cut-based tau isolation (rawIso)
      self.out.idAntiEle_3[0]              = maxtau.idAntiEle
      self.out.idAntiMu_3[0]               = maxtau.idAntiMu
      self.out.idMVAoldDM2017v2_3[0]       = maxtau.idMVAoldDM2017v2
      self.out.idMVAnewDM2017v2_3[0]       = maxtau.idMVAnewDM2017v2
      self.out.idDeepTau2017v2p1VSe_3[0]   = maxtau.idDeepTau2017v2p1VSe
      self.out.idDeepTau2017v2p1VSmu_3[0]  = maxtau.idDeepTau2017v2p1VSmu
      self.out.idDeepTau2017v2p1VSjet_3[0] = maxtau.idDeepTau2017v2p1VSjet
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
      self.out.idAntiEle_3[0]              = -1
      self.out.idAntiMu_3[0]               = -1
      self.out.idMVAoldDM2017v2_3[0]       = -1
      self.out.idMVAnewDM2017v2_3[0]       = -1
      self.out.idDeepTau2017v2p1VSe_3[0]   = -1
      self.out.idDeepTau2017v2p1VSmu_3[0]  = -1
      self.out.idDeepTau2017v2p1VSjet_3[0] = -1
      self.out.iso_3[0]                    = -1
      self.out.jpt_match_3[0]              = -1
      self.out.jpt_genmatch_3[0]           = -1
      if self.ismc:
        self.out.jpt_genmatch_3[0]         = -1
        self.out.genmatch_3[0]             = -1
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = electron.genPartFlav
      self.out.genmatch_2[0] = muon.genPartFlav
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,electron,muon)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBraches(event,jets,met,njets_vars,met_vars)
      if electron.pfRelIso03_all<0.50 and muon.pfRelIso04_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # MUON WEIGHTS
      self.out.trigweight[0]        = self.muSFs.getTriggerSF(electron.pt,electron.eta)
      self.out.idisoweight_1[0]     = self.muSFs.getIdIsoSF(electron.pt,electron.eta)
      self.out.idisoweight_2[0]     = self.muSFs.getIdIsoSF(muon.pt,muon.eta)
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,electron,muon,met,met_vars)
    
    
    self.out.fill()
    return True
    
