# Author: Izaak Neutelings (June 2020)
# Description: Simple module to pre-select mutau events
import sys
import numpy as np
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.analysis.TreeProducerETau import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonTauPair, loosestIso, idIso, matchgenvistau, matchtaujet
from TauFW.PicoProducer.corrections.ElectronSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import TrigObjMatcher
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool, TauFESTool


class ModuleETau(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'etau'
    super(ModuleETau,self).__init__(fname,**kwargs)
    self.out = TreeProducerETau(fname,self)
    self.resoScale = 0.
   
    # TRIGGERS
    
    print("---> YEAR: ", self.year)
    print("---> ERA: ", self.era)
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger   = TrigObjMatcher(jsonfile,trigger='SingleElectron',isdata=self.isdata)
    self.eleCutPt  = self.trigger.ptmins[0]
    self.tauCutPt  = 20
    self.eleCutEta = 2.1
    self.tauCutEta = 2.3
    #print("EES: ", self.ees) 
    # CORRECTIONS
    if self.ismc:
      self.eleSFs  = ElectronSFs(era=self.era) # electron id/iso/trigger SFs
      #allowed_wp=['Loose','Medium','Tight','VTight']
      #allowed_wp_vsele=['VVLoose','Tight']

      #####################################################################
      ## UL TAU ID SF DeepTau2018v2p5 #####################################
      ####VSjet Medium 
      ##  VSele VVL 
      self.tesTool = TauESTool(self.era, id='DeepTau2018v2p5VSjet',wp='Medium', wp_vsele='VVLoose') # real tau energy scale corrections
      self.tauSFs  = TauIDSFTool(self.era,'DeepTau2018v2p5VSjet',wp='Medium', wp_vsele='VVLoose', ptdm=True)
      ## If you intend to use different DeepTau WPs change the SFs accordingly
      ## in this section here 
      ####################################################################
      
      #self.fesTool = TauFESTool(tauSFVersion[self.year]) # e -> tau fake energy scale
      #self.etfSFs  = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSe',  'VLoose')
      #self.mtfSFs  = TauIDSFTool(tauSFVersion[self.year],'DeepTau2017v2p1VSmu', 'VLoose')
      self.resoScale = 0.1


    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('electron',     "electron"                   )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleETau,self).beginJob()
    print(">>> %-12s = %s"%('tauwp',      self.tauwp))
    print(">>> %-12s = %s"%('eleCutPt',   self.eleCutPt))
    print(">>> %-12s = %s"%('eleCutEta',  self.eleCutEta))
    print(">>> %-12s = %s"%('tauCutPt',   self.tauCutPt))
    print(">>> %-12s = %s"%('tauCutEta',  self.tauCutEta))
    print(">>> %-12s = %s"%('ZpeekReso',  self.resoScale))
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
    if not self.trigger.fired(event):
      return False
    self.out.cutflow.fill('trig')
    
    
    ##### ELECTRON ###################################
    electrons = [ ]
    for electron in Collection(event,'Electron'):
    #electron energy scale variation
    #ees=1.0 -> pt and mass unchanged
    #ees=1.01 -> pt and mass *1.01 barrel and *1.025 endcap
    #ees=0.99 -> pt and mass *0.99 barrel and *0.975 endcap
      if self.ismc and self.ees!=1:
        if abs(electron.eta)<1.5 :
          electron.pt   *= self.ees
          electron.mass *= self.ees
        elif self.ees==1.01 :
          electron.pt   *= 1.025
          electron.mass *= 1.025
        else :
          electron.pt   *= 0.975
          electron.mass *= 0.975
      if electron.pt<self.eleCutPt: continue
      if abs(electron.eta)>self.eleCutEta: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if not electron.convVeto: continue
      if electron.lostHits>1: continue
      if electron.pfRelIso03_all > 0.5: continue 
      if not (electron.mvaFall17V2Iso_WP90 or electron.mvaFall17V2noIso_WP90): continue
      if not self.trigger.match(event,electron): continue
      electrons.append(electron)
    if len(electrons)==0:
      return False
    self.out.cutflow.fill('electron')
    
    
    ##### TAU ########################################
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if abs(tau.eta)>self.tauCutEta: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      #if tau.idDecayModeNewDMs < 0.5: continue
      if abs(tau.charge)!=1: continue
      if tau.idDeepTau2018v2p5VSe<1: continue  # VVVLoose
      if tau.idDeepTau2018v2p5VSmu<1: continue # VLoose
      if tau.idDeepTau2018v2p5VSjet<1: continue
      if self.ismc:
        tes = 1.0
        tau.es   = 1 # store energy scale for propagating to MET
        genmatch = tau.genPartFlav
        if genmatch==5: # real tau
          if self.tes!=None: # user-defined energy scale (for TES studies)
            tes = self.tes
          else: # (apply by default)
            tes = self.tesTool.getTES(tau.pt,tau.decayMode,unc=self.tessys)
            #print("Apply TES to real tauh: ", tes)
          if tes!=1:
            tau.pt   *= tes
            tau.mass *= tes
            tau.es    = tes
        elif self.ltf and 0<genmatch<5: # lepton -> tau fake
          tau.pt   *= self.ltf
          tau.mass *= self.ltf
          tau.es    = self.ltf
        elif self.fes and genmatch in [1,3]: # electron -> tau fake (apply by default, override with 'ltf=1.0')
          #fes = self.fesTool.getFES(tau.eta,tau.decayMode,unc=self.fes)
          #fes = 1.0
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
    
    
    ##### ETAU PAIR ##################################
    ltaus = [ ]
    for electron in electrons:
      for tau in taus:
        if tau.DeltaR(electron)<0.5: continue
        ltau = LeptonTauPair(electron,electron.pfRelIso03_all,tau,tau.rawDeepTau2018v2p5VSjet)
        ltaus.append(ltau)
    
    if len(ltaus)==0:
      return False
    electron, tau = max(ltaus).pair
    electron.tlv  = electron.p4()
    tau.tlv       = tau.p4()
    self.out.cutflow.fill('pair')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[electron],[ ],[tau],self.channel)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[electron],[ ],[ ],self.channel)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # ELECTRON
    self.out.pt_1[0]                       = electron.pt
    self.out.eta_1[0]                      = electron.eta
    self.out.phi_1[0]                      = electron.phi
    self.out.m_1[0]                        = electron.mass
    self.out.y_1[0]                        = electron.tlv.Rapidity()
    self.out.dxy_1[0]                      = electron.dxy
    self.out.dz_1[0]                       = electron.dz
    self.out.q_1[0]                        = electron.charge
    self.out.iso_1[0]                      = electron.pfRelIso03_all
    self.out.cutBased_1[0]                 = electron.cutBased
    self.out.mvaFall17Iso_WP90_1[0]        = electron.mvaFall17V2Iso_WP90
    self.out.mvaFall17Iso_WP80_1[0]        = electron.mvaFall17V2Iso_WP80
    self.out.mvaFall17noIso_WP90_1[0]      = electron.mvaFall17V2noIso_WP90
    self.out.mvaFall17noIso_WP80_1[0]      = electron.mvaFall17V2noIso_WP80
    
    
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
  #  self.out.iso_2[0]                      = tau.rawIso
  #  self.out.idiso_2[0]                    = idIso(tau) # cut-based tau isolation (rawIso)
  #  self.out.rawAntiEle_2[0]               = tau.rawAntiEle
  #  self.out.rawMVAoldDM2017v2_2[0]        = tau.rawMVAoldDM2017v2
  #  self.out.rawMVAnewDM2017v2_2[0]        = tau.rawMVAnewDM2017v2
    self.out.rawDeepTau2017v2p1VSe_2[0]    = tau.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau.rawDeepTau2017v2p1VSjet
    self.out.rawDeepTau2018v2p5VSe_2[0]    = tau.rawDeepTau2018v2p5VSe
    self.out.rawDeepTau2018v2p5VSmu_2[0]   = tau.rawDeepTau2018v2p5VSmu
    self.out.rawDeepTau2018v2p5VSjet_2[0]  = tau.rawDeepTau2018v2p5VSjet

 #   self.out.idAntiEle_2[0]                = tau.idAntiEle
 #   self.out.idAntiMu_2[0]                 = tau.idAntiMu
    self.out.idDecayMode_2[0]              = tau.idDecayMode
 #  self.out.idDecayModeNewDMs_2[0]        = tau.idDecayModeNewDMs
 #   self.out.idMVAoldDM2017v2_2[0]         = tau.idMVAoldDM2017v2
 #   self.out.idMVAnewDM2017v2_2[0]         = tau.idMVAnewDM2017v2
    self.out.idDeepTau2017v2p1VSe_2[0]     = tau.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_2[0]    = tau.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_2[0]   = tau.idDeepTau2017v2p1VSjet
    self.out.idDeepTau2018v2p5VSe_2[0]     = tau.idDeepTau2018v2p5VSe
    self.out.idDeepTau2018v2p5VSmu_2[0]    = tau.idDeepTau2018v2p5VSmu
    self.out.idDeepTau2018v2p5VSjet_2[0]   = tau.idDeepTau2018v2p5VSjet
 #   self.out.chargedIso_2[0]               = tau.chargedIso
 #   self.out.neutralIso_2[0]               = tau.neutralIso
 #   self.out.leadTkPtOverTauPt_2[0]        = tau.leadTkPtOverTauPt
 #   self.out.photonsOutsideSignalCone_2[0] = tau.photonsOutsideSignalCone
 #   self.out.puCorr_2[0]                   = tau.puCorr
    
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = electron.genPartFlav
      self.out.genmatch_2[0] = tau.genPartFlav
      pt, eta, phi, status       = matchgenvistau(event,tau)
      self.out.genvistaupt_2[0]  = pt
      self.out.genvistaueta_2[0] = eta
      self.out.genvistauphi_2[0] = phi
      self.out.gendm_2[0]        = status
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,electron,tau)
    if self.ismc:
      self.out.jpt_match_2[0], self.out.jpt_genmatch_2[0] = matchtaujet(event,tau,self.ismc)
    else:
      self.out.jpt_match_2[0] = matchtaujet(event,tau,self.ismc)[0]
    
    
    # WEIGHTS

    if self.ismc:
      self.out.genweight[0] = 1.0
      self.out.trigweight[0] = 1.0
      self.out.idisoweight_1[0] = 1.0
      self.out.idweight_2[0] = 1.0
      self.out.ltfweight_2[0] = 1.0
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if electron.pfRelIso03_all<0.50 and tau.idDeepTau2018v2p5VSjet>=2:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # ELECTRON WEIGHTS
      self.out.trigweight[0]              = self.eleSFs.getTriggerSF(electron.pt,electron.eta)
      self.out.idisoweight_1[0]           = self.eleSFs.getIdIsoSF(electron.pt,electron.eta)
      #print("pt:  eta: IDISO weight:")
      #print(tau.pt, tau.eta, self.out.idisoweight_1[0]) 
      # TAU WEIGHTS
      if tau.genPartFlav==5: # real tau
        self.out.idweight_2[0]               = self.tauSFs.getSFvsDMandPT(tau.pt, tau.decayMode)
        if self.dosys:
          self.out.idweightUp_2[0]          = self.tauSFs.getSFvsDMandPT(tau.pt, tau.decayMode,unc='syst_alldms_'+str(self.year)+'_up')
          self.out.idweightDown_2[0]        = self.tauSFs.getSFvsDMandPT(tau.pt, tau.decayMode,unc='syst_alldms_'+str(self.year)+'_down')
      #elif tau.genPartFlav in [1,3]: # muon -> tau fake
      #  self.out.ltfweight_2[0]             = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav)
      #  if self.dosys:
      #    self.out.ltfweightUp_2[0]         = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Up')
      #    self.out.ltfweightDown_2[0]       = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Down')
      #elif tau.genPartFlav in [2,4]: # electron -> tau fake
      #  self.out.ltfweight_2[0]             = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav)
      #  if self.dosys:
      #    self.out.ltfweightUp_2[0]         = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Up')
      #    self.out.ltfweightDown_2[0]       = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav,unc='Down')
      self.out.weight[0]        = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0] #*self.out.idisoweight_2[0]
    elif self.isembed:
      ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
      self.out.genweight[0]     = event.genWeight
      self.out.trackweight[0]   = 0.975 if tau.decayMode==0 else 1.0247 if tau.decayMode==1 else 0.927 if tau.decayMode==10 else 0.974 if tau.decayMode==11 else 1.0
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,electron,tau,met,met_vars)
    if self.ismc :
      self.out.m_vis_resoUp   = 90.99 + (1+self.resoScale)*(self.out.m_vis-90.99)
      self.out.m_vis_resoDown = 90.99 + (1-self.resoScale)*(self.out.m_vis-90.99)
    #print ">>> %-12s = %s"%('mvis',      self.out.m_vis)
    
    self.out.fill()
    return True
