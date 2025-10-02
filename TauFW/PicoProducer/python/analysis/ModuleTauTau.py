# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select mutau events
import sys
import numpy as np
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.analysis.TreeProducerTauTau import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import DiTauPair, loosestIso, idIso, matchgenvistau, matchtaujet
from TauFW.PicoProducer.corrections.TrigObjMatcher import TrigObjMatcher
from TauFW.PicoProducer.corrections.TauTriggerSFs import TauTriggerSFs
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool, TauFESTool


class ModuleTauTau(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mutau'
    super(ModuleTauTau,self).__init__(fname,**kwargs)
    self.out = TreeProducerTauTau(fname,self)
    
    # TRIGGERS
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger   = TrigObjMatcher(jsonfile,trigger='ditau',isdata=self.isdata)
    self.tauCutPt  = 40
    self.tauCutEta = 2.1
    
    # CORRECTIONS
    if self.ismc:
      self.trigTool       = TauTriggerSFs('tautau','Medium',year=self.year)
      self.trigTool_tight = TauTriggerSFs('tautau','Tight', year=self.year)
      self.tesTool        = TauESTool(tauSFVersion[self.year]) # real tau energy scale
      self.fesTool        = TauFESTool(tauSFVersion[self.year]) # e -> tau fake energy scale
      self.tauSFs         = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSjet','Medium',dm=True)
      self.tauSFs_tight   = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSjet','Tight',dm=True)
      self.etfSFs         = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSe', 'VVLoose')
      self.mtfSFs         = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSmu','Loose')
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                      )
    self.out.cutflow.addcut('trig',         "trigger"                     )
    self.out.cutflow.addcut('tau',          "tau"                         )
    self.out.cutflow.addcut('pair',         "ditau pair"                  )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15        )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16  ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleTauTau,self).beginJob()
    print(">>> %-12s = %s"%('tauwp',     self.tauwp))
    print(">>> %-12s = %s"%('tauCutPt',  self.tauCutPt))
    print(">>> %-12s = %s"%('tauCutEta', self.tauCutEta))
    print(">>> %-12s = '%s'"%('triggers',self.trigger.path.replace("||","\n>>> %s||"%(' '*16))))
    
  
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
    
    
    ##### TAU ########################################
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if abs(tau.eta)>self.tauCutEta: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      if tau.idDeepTau2017v2p1VSe<1: continue   # VVVLoose
      if tau.idDeepTau2017v2p1VSmu<1: continue  # VLoose
      if tau.idDeepTau2017v2p1VSjet<self.tauwp: continue
      if self.ismc:
        tau.es   = 1 # store energy scale for propagating to MET
        genmatch = tau.genPartFlav
        if genmatch==5: # real tau
          if self.tes!=None: # user-defined energy scale (for TES studies)
            tes = self.tes
          else: # (apply by default)
            tes = self.tesTool.getTES(tau.pt,tau.decayMode,unc=self.tessys)
          if tes!=1:
            tau.pt   *= tes
            tau.mass *= tes
            tau.es    = tes
        elif self.ltf and 0<genmatch<5: # lepton -> tau fake
          tau.pt   *= self.ltf
          tau.mass *= self.ltf
          tau.es    = self.ltf
        elif genmatch in [1,3]: # electron -> tau fake (apply by default, override with 'ltf=1.0')
          fes = self.fesTool.getFES(tau.eta,tau.decayMode,unc=self.fes)
          tau.pt   *= fes
          tau.mass *= fes
          tau.es    = fes
        elif self.jtf!=1.0 and genmatch==0: # jet -> tau fake
          tau.pt   *= self.jtf
          tau.mass *= self.jtf
          tau.es    = self.jtf
      if tau.pt<self.tauCutPt: continue
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    
    
    ##### DITAU PAIR #################################
    ditaus = [ ]
    for i, tau1 in enumerate(taus,1):
      for tau2 in taus[i:]:
        if tau1.DeltaR(tau2)<0.5: continue
        ditau = DiTauPair(tau1,tau1.rawDeepTau2017v2p1VSjet,tau2,tau2.rawDeepTau2017v2p1VSjet)
        ditaus.append(ditau)
    if len(ditaus)==0:
      return False
    tau1, tau2 = max(ditaus).pair
    tau1.tlv   = tau1.p4()
    tau2.tlv   = tau2.p4()
    self.out.cutflow.fill('pair')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ ],[ ],[tau1,tau2],self.channel)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[ ],[ ],[ ],self.channel)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] #or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto #or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # TAU 1
    self.out.pt_1[0]                       = tau1.pt
    self.out.eta_1[0]                      = tau1.eta
    self.out.phi_1[0]                      = tau1.phi
    self.out.m_1[0]                        = tau1.mass
    self.out.y_1[0]                        = tau1.tlv.Rapidity()
    self.out.dxy_1[0]                      = tau1.dxy
    self.out.dz_1[0]                       = tau1.dz
    self.out.q_1[0]                        = tau1.charge
    self.out.dm_1[0]                       = tau1.decayMode
    self.out.iso_1[0]                      = tau1.rawIso
    self.out.idiso_1[0]                    = idIso(tau1) # cut-based tau isolation (rawIso)
    self.out.rawDeepTau2017v2p1VSe_1[0]    = tau1.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_1[0]   = tau1.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_1[0]  = tau1.rawDeepTau2017v2p1VSjet
    self.out.idAntiEle_1[0]                = tau1.idAntiEle
    self.out.idAntiMu_1[0]                 = tau1.idAntiMu
    self.out.idDecayMode_1[0]              = tau1.idDecayMode
    self.out.idDecayModeNewDMs_1[0]        = tau1.idDecayModeNewDMs
    self.out.idMVAoldDM2017v2_1[0]         = tau1.idMVAoldDM2017v2
    self.out.idMVAnewDM2017v2_1[0]         = tau1.idMVAnewDM2017v2
    self.out.idDeepTau2017v2p1VSe_1[0]     = tau1.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_1[0]    = tau1.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_1[0]   = tau1.idDeepTau2017v2p1VSjet
    self.out.chargedIso_1[0]               = tau1.chargedIso
    self.out.neutralIso_1[0]               = tau1.neutralIso
    self.out.leadTkPtOverTauPt_1[0]        = tau1.leadTkPtOverTauPt
    self.out.photonsOutsideSignalCone_1[0] = tau1.photonsOutsideSignalCone
    self.out.puCorr_1[0]                   = tau1.puCorr
    
    
    # TAU 2
    self.out.pt_2[0]                       = tau2.pt
    self.out.eta_2[0]                      = tau2.eta
    self.out.phi_2[0]                      = tau2.phi
    self.out.m_2[0]                        = tau2.mass
    self.out.y_2[0]                        = tau2.tlv.Rapidity()
    self.out.dxy_2[0]                      = tau2.dxy
    self.out.dz_2[0]                       = tau2.dz
    self.out.q_2[0]                        = tau2.charge
    self.out.dm_2[0]                       = tau2.decayMode
    self.out.iso_2[0]                      = tau2.rawIso
    self.out.idiso_2[0]                    = idIso(tau2) # cut-based tau isolation (rawIso)
    self.out.rawDeepTau2017v2p1VSe_2[0]    = tau2.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau2.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau2.rawDeepTau2017v2p1VSjet
    self.out.idAntiEle_2[0]                = tau2.idAntiEle
    self.out.idAntiMu_2[0]                 = tau2.idAntiMu
    self.out.idDecayMode_2[0]              = tau2.idDecayMode
    self.out.idDecayModeNewDMs_2[0]        = tau2.idDecayModeNewDMs
    self.out.idMVAoldDM2017v2_2[0]         = tau2.idMVAoldDM2017v2
    self.out.idMVAnewDM2017v2_2[0]         = tau2.idMVAnewDM2017v2
    self.out.idDeepTau2017v2p1VSe_2[0]     = tau2.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_2[0]    = tau2.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_2[0]   = tau2.idDeepTau2017v2p1VSjet
    self.out.chargedIso_2[0]               = tau2.chargedIso
    self.out.neutralIso_2[0]               = tau2.neutralIso
    self.out.leadTkPtOverTauPt_2[0]        = tau2.leadTkPtOverTauPt
    self.out.photonsOutsideSignalCone_2[0] = tau2.photonsOutsideSignalCone
    self.out.puCorr_2[0]                   = tau2.puCorr
    
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0]     = tau1.genPartFlav
      self.out.genmatch_2[0]     = tau2.genPartFlav
      pt1, eta1, phi1, status1   = matchgenvistau(event,tau1)
      pt2, eta2, phi2, status2   = matchgenvistau(event,tau2)
      self.out.genvistaupt_1[0]  = pt1
      self.out.genvistaueta_1[0] = eta1
      self.out.genvistauphi_1[0] = phi1
      self.out.gendm_1[0]        = status1
      self.out.genvistaupt_2[0]  = pt2
      self.out.genvistaueta_2[0] = eta2
      self.out.genvistauphi_2[0] = phi2
      self.out.gendm_2[0]        = status2
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,tau1,tau2)
    self.out.jpt_match_1[0], self.out.jpt_genmatch_1[0] = matchtaujet(event,tau1,self.ismc)
    self.out.jpt_match_2[0], self.out.jpt_genmatch_2[0] = matchtaujet(event,tau2,self.ismc)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if tau1.idDeepTau2017v2p1VSjet>=2 and tau2.idDeepTau2017v2p1VSjet>=2:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      self.out.trigweight[0]             = self.trigTool.getSFPair(tau1,tau2)
      self.out.trigweight_tight[0]       = self.trigTool_tight.getSFPair(tau1,tau2)
      if self.dosys:
        self.out.trigweightUp[0]         = self.trigTool.getSFPair(tau1,tau2,unc='Up')
        self.out.trigweightDown[0]       = self.trigTool.getSFPair(tau1,tau2,unc='Down')
      
      # DEFAULTS
      self.out.idweight_1[0]        = 1.
      self.out.idweight_2[0]        = 1.
      self.out.idweight_tight_1[0]  = 1.
      self.out.idweight_tight_2[0]  = 1.
      self.out.ltfweight_2[0]       = 1.
      self.out.ltfweight_2[0]       = 1.
      if self.dosys:
        self.out.idweightUp_1[0]    = 1.
        self.out.idweightUp_2[0]    = 1.
        self.out.idweightDown_1[0]  = 1.
        self.out.idweightDown_2[0]  = 1.
        self.out.ltfweightUp_1[0]   = 1.
        self.out.ltfweightUp_2[0]   = 1.
        self.out.ltfweightDown_1[0] = 1.
        self.out.ltfweightDown_2[0] = 1.
      
      # TAU 1 WEIGHTS
      if tau1.genPartFlav==5:
        self.out.idweight_1[0]        = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode)
        self.out.idweight_tight_1[0]  = self.tauSFs_tight.getSFvsDM(tau1.pt,tau1.decayMode)
        if self.dosys:
          self.out.idweightUp_1[0]    = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode,unc='Up')
          self.out.idweightDown_1[0]  = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode,unc='Down')
      elif tau1.genPartFlav>0:
        ltfTool = self.etfSFs if tau1.genPartFlav in [1,3] else self.mtfSFs
        self.out.ltfweight_1[0]       = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav)
        if self.dosys:
          self.out.ltfweightUp_1[0]   = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav,unc='Up')
          self.out.ltfweightDown_1[0] = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav,unc='Down')
      
      # TAU 2 WEIGHTS
      if tau1.genPartFlav==5:
        self.out.idweight_2[0]        = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode)
        self.out.idweight_tight_2[0]  = self.tauSFs_tight.getSFvsDM(tau1.pt,tau1.decayMode)
        if self.dosys:
          self.out.idweightUp_2[0]    = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode,unc='Up')
          self.out.idweightDown_2[0]  = self.tauSFs.getSFvsDM(tau1.pt,tau1.decayMode,unc='Down')
      elif tau1.genPartFlav>0:
        ltfTool = self.etfSFs if tau1.genPartFlav in [1,3] else self.mtfSFs
        self.out.ltfweight_2[0]       = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav)
        if self.dosys:
          self.out.ltfweightUp_2[0]   = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav,unc='Up')
          self.out.ltfweightDown_2[0] = ltfTool.getSFvsEta(tau1.eta,tau1.genPartFlav,unc='Down')
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,tau1,tau2,met,met_vars)
    
    
    self.out.fill()
    return True
    
