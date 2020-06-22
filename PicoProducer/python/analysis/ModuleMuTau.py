# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select mutau events
import sys
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from TauFW.PicoProducer.analysis.TreeProducerMuTau import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonTauPair, loosestIso, idIso
from TauFW.PicoProducer.corrections.MuonSFs import *
#from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
#from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool


class ModuleMuTau(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mutau'
    super(ModuleMuTau,self).__init__(fname,**kwargs)
    self.out = TreeProducerMuTau(fname,self)
    
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
    self.tauCutPt     = 20
    self.tauCutEta    = 2.3
    
    # CORRECTIONS
    if self.ismc:
      self.muSFs      = MuonSFs(year=self.year)
    #  self.tauSFs     = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSjet','Tight')
    #  self.tauSFvsDM  = TauIDSFTool_DM(tauSFVersion[self.year],'DeepTau2017v2p1VSjet','Tight')
    #  self.tesTool    = TauESTool(tauSFVersion[self.year])
    #  self.etfSFs     = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSe', 'VLoose')
    #  self.etfSFs_VVL = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSe', 'VVLoose')
    #  self.etfSFs_T   = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSe', 'Tight')
    #  self.mtfSFs     = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSmu','Tight')
    #  self.mtfSFs_VL  = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSmu','VLoose')
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 )
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleMuTau,self).beginJob()
    print ">>> %-12s = %s"%('muonCutPt',  self.muonCutPt)
    print ">>> %-12s = %s"%('muonCutEta', self.muonCutEta)
    print ">>> %-12s = %s"%('tauCutPt',   self.tauCutPt)
    print ">>> %-12s = %s"%('tauCutEta',  self.tauCutEta)
    pass
    
  
  def analyze(self, event):
    """Process and select events; fill branches and return True if the events passes,
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
    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt < self.muonCutPt(event): continue
      if abs(muon.eta) > self.muonCutEta(event): continue
      if abs(muon.dz) > 0.2: continue
      if abs(muon.dxy) > 0.045: continue
      if not muon.mediumId: continue
      #if muon.pfRelIso04_all>0.50: continue
      muons.append(muon)    
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    
    
    ##### TAU ########################################
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if abs(tau.eta)>self.tauCutEta: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      #if self.ismc:
      #  genmatch = tau.genPartFlav #ord(tau.genPartFlav)
      #  if genmatch==5:
      #    tes = 1
      #    if self.tes!=None:
      #      tes *= self.tes
      #    else:
      #      tes *= self.tesTool.getTES(tau.pt,tau.decayMode,unc=self.tesSys)
      #    if tes!=1:
      #      tau.pt   *= tes
      #      tau.mass *= tes
      #  elif self.ltf!=1.0 and 0<genmatch<5:
      #    tau.pt   *= self.ltf
      #    tau.mass *= self.ltf
      #  elif self.jtf!=1.0 and genmatch==0:
      #    tau.pt   *= self.jtf
      #    tau.mass *= self.jtf
      if tau.pt<self.tauCutPt: continue
      ###if tau.idAntiEle<1: continue
      ###if tau.idAntiMu<1: continue
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    
    
    ##### MUTAU PAIR #################################
    ltaus = [ ]
    for muon in muons:
      for tau in taus:
        if tau.DeltaR(muon)<0.5: continue
        ltau = LeptonTauPair(muon,muon.pfRelIso04_all,tau,tau.rawDeepTau2017v2p1VSjet)
        ltaus.append(ltau)
    if len(ltaus)==0:
      return False
    muon, tau = max(ltaus).pair
    muon.tlv  = muon.p4()
    tau.tlv   = tau.p4()
    self.out.cutflow.fill('pair')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getLeptonVetoes(event,[ ],[muon],[tau],self.channel)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getLeptonVetoes(event,[ ],[muon],[ ],self.channel)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # MUON
    self.out.pt_1[0]                       = muon.pt
    self.out.eta_1[0]                      = muon.eta
    self.out.phi_1[0]                      = muon.phi
    self.out.m_1[0]                        = muon.mass
    self.out.y_1[0]                        = muon.tlv.Rapidity()
    self.out.dxy_1[0]                      = muon.dxy
    self.out.dz_1[0]                       = muon.dz
    self.out.q_1[0]                        = muon.charge
    self.out.iso_1[0]                      = muon.pfRelIso04_all
    
    
    # TAU
    self.out.pt_2[0]                       = tau.pt
    self.out.eta_2[0]                      = tau.eta
    self.out.phi_2[0]                      = tau.phi
    self.out.m_2[0]                        = tau.mass
    self.out.y_2[0]                        = tau.tlv.Rapidity()
    self.out.dxy_2[0]                      = tau.dxy
    self.out.dz_2[0]                       = tau.dz
    self.out.q_2[0]                        = tau.charge
    self.out.dm_2[0]                       = tau.decayMode
    self.out.iso_2[0]                      = tau.rawIso
    self.out.idiso_2[0]                    = idIso(tau) # cut-based tau isolation (rawIso)
    self.out.rawAntiEle_2[0]               = tau.rawAntiEle
    self.out.rawMVAoldDM2017v2_2[0]        = tau.rawMVAoldDM2017v2
    self.out.rawMVAnewDM2017v2_2[0]        = tau.rawMVAnewDM2017v2
    self.out.rawDeepTau2017v2p1VSe_2[0]    = tau.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau.rawDeepTau2017v2p1VSjet
    self.out.idAntiEle_2[0]                = tau.idAntiEle
    self.out.idAntiMu_2[0]                 = tau.idAntiMu
    self.out.idDecayMode_2[0]              = tau.idDecayMode
    self.out.idDecayModeNewDMs_2[0]        = tau.idDecayModeNewDMs
    self.out.idMVAoldDM2017v2_2[0]         = tau.idMVAoldDM2017v2
    self.out.idMVAnewDM2017v2_2[0]         = tau.idMVAnewDM2017v2
    self.out.idDeepTau2017v2p1VSe_2[0]     = tau.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_2[0]    = tau.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_2[0]   = tau.idDeepTau2017v2p1VSjet
    self.out.chargedIso_2[0]               = tau.chargedIso
    self.out.neutralIso_2[0]               = tau.neutralIso
    self.out.leadTkPtOverTauPt_2[0]        = tau.leadTkPtOverTauPt
    self.out.photonsOutsideSignalCone_2[0] = tau.photonsOutsideSignalCone
    self.out.puCorr_2[0]                   = tau.puCorr
    
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = muon.genPartFlav
      self.out.genmatch_2[0] = tau.genPartFlav
      dRmin    = 0.5
      taumatch = None
      for genvistau in Collection(event,'GenVisTau'):
        dR = genvistau.DeltaR(tau)
        if dR<dRmin:
          dRmin    = dR
          taumatch = genvistau
      if taumatch:
        self.out.genvistaupt_2[0]  = taumatch.pt
        self.out.genvistaueta_2[0] = taumatch.eta
        self.out.genvistauphi_2[0] = taumatch.phi
        self.out.gendm_2[0]        = taumatch.status
      else:
        self.out.genvistaupt_2[0]  = -1
        self.out.genvistaueta_2[0] = -9
        self.out.genvistauphi_2[0] = -9
        self.out.gendm_2[0]        = -1
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,muon,tau)
    if tau.jetIdx>=0:
      self.out.jpt_match_2[0] = event.Jet_pt[tau.jetIdx]
      if self.ismc:
        if event.Jet_genJetIdx[tau.jetIdx]>=0:
          self.out.jpt_genmatch_2[0] = event.GenJet_pt[event.Jet_genJetIdx[tau.jetIdx]]
        else:
          self.out.jpt_genmatch_2[0] = -1
    else:
      self.out.jpt_match_2[0] = -1
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBraches(event,jets,met,njets_vars,met_vars)
      if loosestIso(tau) and muon.pfRelIso04_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # MUON WEIGHTS
      self.out.trigweight[0]              = self.muSFs.getTriggerSF(muon.pt,muon.eta)
      self.out.idisoweight_1[0]           = self.muSFs.getIdIsoSF(muon.pt,muon.eta)
      
    #  # DEFAULTS
    #  self.out.idweight_2[0]              = 1.
    #  self.out.ltfweight_2[0]             = 1.
    #  if not self.doTight:
    #    self.out.idweightUp_2[0]          = 1.
    #    self.out.idweightDown_2[0]        = 1.
    #    self.out.ltfweightUp_2[0]         = 1.
    #    self.out.ltfweightDown_2[0]       = 1.
    #  
    #  # TAU WEIGHTS
    #  if tau.genPartFlav==5:
    #    self.out.idweight_2[0]              = self.tauSFs.getSFvsPT(tau.pt)
    #    if not self.doTight:
    #      self.out.idweightUp_2[0]          = self.tauSFs.getSFvsPT(tau.pt,unc='Up')
    #      self.out.idweightDown_2[0]        = self.tauSFs.getSFvsPT(tau.pt,unc='Down')
    #  elif tau.genPartFlav in [1,3]:
    #    self.out.ltfweight_2[0]             = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav)
    #    if not self.doTight:
    #      self.out.ltfweightUp_2[0]         = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Up')
    #      self.out.ltfweightDown_2[0]       = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Down')')
    #  elif tau.genPartFlav in [2,4]:
    #    self.out.ltfweight_2[0]             = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav)
    #    if not self.doTight:
    #      self.out.ltfweightUp_2[0]         = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Up')
    #      self.out.ltfweightDown_2[0]       = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Down')
    #  #elif 0<tau.genPartFlav<5:
    #  #  ltfTool = self.etfSFs if tau.genPartFlav in [1,3] else self.mtfSFs
    #  #  self.out.ltfweight_2[0]         = ltfTool.getSFvsEta(tau.eta,tau.genPartFlav)
    #  #  if not self.doTight:
    #  #    self.out.ltfweightUp_2[0]     = ltfTool.getSFvsEta(tau.eta,tau.genPartFlav,unc='Up')
    #  #    self.out.ltfweightDown_2[0]   = ltfTool.getSFvsEta(tau.eta,tau.genPartFlav,unc='Down')
    #  
    #  self.out.weight[0]        = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0] #*self.out.idisoweight_2[0]
    #elif self.isEmbed:
    #  ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
    #  self.out.genweight[0]     = event.genWeight
    #  self.out.trackweight[0]   = 0.975 if tau.decayMode==0 else 1.0247 if tau.decayMode==1 else 0.927 if tau.decayMode==10 else 0.974 if tau.decayMode==11 else 1.0
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,muon.tlv,tau.tlv,met,met_vars)
    
    
    self.out.fill()
    return True
    
