# Author: Filip Bilandzija (Oct 2025)
# Description: Simple module to pre-select etau events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerETau import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonTauPair, loosestIso, idIso, matchgenvistau, matchtaujet, filtermutau
from TauFW.PicoProducer.corrections.ElectronSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool
import ROOT
from ROOT import TVector2, TMath

def deltaR(eta1, eta2, phi1, phi2):
    deta = eta1 - eta2
    dphi = TVector2.Phi_mpi_pi(phi1 - phi2)
    return TMath.Sqrt(deta*deta + dphi*dphi)

def has_filter_bit(bits, bit):
    return (bits & (1 << bit)) != 0

class ModuleETau_trig(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mutau'
    super(ModuleETau_trig,self).__init__(fname,**kwargs)
    self.out = TreeProducerETau(fname,self)
    print("=====> ERA: ", self.era)
    print("=====> YEAR: ", self.year) 
    # TRIGGERS
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger   = TrigObjMatcher(jsonfile,trigger='SingleElectron',isdata=self.isdata)
    if self.year==2024 or self.year == 2025:
      # self.trigger    = lambda e: e.HLT_Ele30_WPTight_Gsf #e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
    #   self.trigger    = lambda e: True
      self.eleCutPt  = 32
      self.eleCutEta = 2.1
    else:
      # self.trigger    = lambda e: e.HLT_Ele32_WPTight_Gsf
      self.eleCutPt  = 32
      self.eleCutEta = 2.1
    self.tauCutPt     = 20
    self.tauCutEta    = 2.5 # 2.3 DeepTau2p1 and 2.5 for DeepTau2p5

    
    # CORRECTIONS
    if self.ismc:
      if self.year==2024 or self.year == 2025:
        self.eleSFs  = 1
      else:
        self.eleSFs   = ElectronSFs(era=self.era,verb=self.verbosity) # electron id/iso/trigger SFs
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('electron',         "electron"                       )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('pair',         "pair"                       )
    #self.out.cutflow.addcut('electronveto',     "electron veto"                  )
    #self.out.cutflow.addcut('elecveto',     "electron veto"              )
    self.out.cutflow.addcut('lepvetoes',     "lep vetoes"              )
    self.out.cutflow.addcut('jetvetoes',     "jet vetoes"              )
    self.out.cutflow.addcut('btag_veto',     "btag veto"              )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    ## Important cutflow entries to make stitching with exclusive mutauh sample
    self.out.cutflow.addcut('weight_mutaufilter', "no cut, mutaufilter", 17 )    
    self.out.cutflow.addcut('weight_mutaufilter_NUP0orp4', "no cut, weighted, mutau, 0 or >4 jets", 18 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP1', "no cut, weighted, mutau, 1 jet", 19 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP2', "no cut, weighted, mutau, 2 jets", 20 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP3', "no cut, weighted, mutau, 3 jets", 21 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP4', "no cut, weighted, mutau, 4 jets", 22 )

  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleETau_trig,self).beginJob()
    print(">>> %-12s = %s"%('tauwp',      self.tauwp))
    print(">>> %-12s = %s"%('eleCutPt',  self.eleCutPt))
    print(">>> %-12s = %s"%('eleCutEta', self.eleCutEta))
    print(">>> %-12s = %s"%('tauCutPt',   self.tauCutPt))
    print(">>> %-12s = %s"%('tauCutEta',  self.tauCutEta))
    pass
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    if not self.fillhists(event):
      return False
    
    
    ##### TRIGGER ####################################
    if self.year not in [2025]:
        if not event.HLT_Ele30_WPTight_Gsf:
            return False
        self.out.cutflow.fill('trig') 
    else:
      self.out.cutflow.fill('trig')   
    ##### ELECTRON ###################################
    electrons = [ ]
    for electron in Collection(event,'Electron'):
    #electron energy scale variation 
      if self.ismc and self.ees!=1:
        electron.pt   *= self.ees
        electron.mass *= self.ees       
      if electron.pt<self.eleCutPt: continue
      if abs(electron.eta)>self.eleCutEta: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if not electron.convVeto: continue
      if electron.lostHits>1: continue
      if electron.pfRelIso03_all > 0.5: continue
      if not electron.mvaNoIso_WP90: continue
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
      if abs(tau.charge)!=1: continue
      #id cuts v2p5
      if tau.idDeepTau2018v2p5VSe<1: continue # VVVLoose
      if tau.idDeepTau2018v2p5VSmu<1: continue # VLoose
      if tau.idDeepTau2018v2p5VSjet<1: continue # VVVLoose
      if self.ismc:
        tau.es   = 1 # store energy scale for propagating to MET
        genmatch = tau.genPartFlav
        if genmatch==5: # real tau
          if self.tes!=None: # user-defined energy scale (for TES studies)
            tes = self.tes
          else: # (apply by default)
            tes = 1 #self.tesTool.getTES(tau.pt,tau.decayMode,unc=self.tessys)
          if tes!=1:
            tau.pt   *= tes
            tau.mass *= tes
            tau.es    = tes
        elif self.ltf and 0<genmatch<5: # lepton -> tau fake
          tau.pt   *= self.ltf
          tau.mass *= self.ltf
          tau.es    = self.ltf
        elif self.jtf!=1.0 and genmatch==0: # jet -> tau fake
          tau.pt   *= self.jtf
          tau.mass *= self.jtf
          tau.es    = self.jtf
      if tau.pt<self.tauCutPt: continue
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    
    
    ##### MUTAU PAIR #################################
  
    ltaus = [ ]
    for electron in electrons:
      for tau in taus:
        if tau.DeltaR(electron)<0.5: continue
        ltau = LeptonTauPair(electron,electron.pfRelIso03_all,tau,tau.rawPNetVSjet)
        ltaus.append(ltau)

    if len(ltaus)==0:
      return False
    electron, tau = max(ltaus).pair
    electron.tlv  = electron.p4()
    tau.tlv       = tau.p4()
    genmatch  = -1 if self.isdata else tau.genPartFlav
    m_vis = (electron.tlv + tau.tlv).M()
    if m_vis < 40 or m_vis > 80:
      return False

    puppimet_vec = ROOT.TVector2(event.PuppiMET_pt, event.PuppiMET_phi)
    ele_vec = ROOT.TVector2(electron.pt, electron.phi)
    mT = TMath.Sqrt(2 * electron.pt * event.PuppiMET_pt * (1 - TMath.Cos(ele_vec.DeltaPhi(puppimet_vec))))
    if mT >= 30:
      return False

    self.out.cutflow.fill('pair')

    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[electron],[ ],[tau],self.channel,era=self.era)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[electron],[ ],[ ],self.channel,era=self.era)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    # self.out.cutflow.fill('eveto')
    # self.out.cutflow.fill('muveto')
    
    
    # VETOS7
    

    #cutflow on veto
    if self.out.lepton_vetoes[0] and self.out.lepton_vetoes_notau[0]: return False
    self.out.cutflow.fill('lepvetoes')

    if self.jetveto(event): return False
    self.out.cutflow.fill('jetvetoes')
   
 
    # EVENT
    self.fillEventBranches(event)
    # if self.year == 2024:
    #   # if not self.ismc:        
    #   #   self.out.Flag_METFilters[0] = event.Flag_METFilters
    #   # if self.ismc:        
    #   self.out.Flag_METFilters[0] = True

    # self.out.Flag_goodVertices[0] = event.Flag_goodVertices
    # self.out.Flag_globalSuperTightHalo2016Filter[0] = event.Flag_globalSuperTightHalo2016Filter
    # self.out.Flag_HBHENoiseFilter[0] = event.Flag_HBHENoiseFilter
    # self.out.Flag_HBHENoiseIsoFilter[0] = event.Flag_HBHENoiseIsoFilter
    # if not self.ismc:
    #     self.out.Flag_eeBadScFilter[0] = event.Flag_eeBadScFilter
    # self.out.Flag_EcalDeadCellTriggerPrimitiveFilter[0] = event.Flag_EcalDeadCellTriggerPrimitiveFilter
    # self.out.Flag_BadPFelectronFilter[0] = event.Flag_BadPFelectronFilter
    # self.out.Flag_BadPFelectronDzFilter[0] = event.Flag_BadPFelectronDzFilter
    # self.out.Flag_ecalBadCalibFilter[0] = event.Flag_ecalBadCalibFilter    
    
    self.out.pass_tag[0] = False
    self.out.pass_probe[0] = False
    if (
        electron.pt > 32 and
        abs(electron.eta) < 2.1 and
        electron.mvaNoIso_WP90 and
        electron.pfRelIso03_all < 0.3 and
        abs(electron.dxy) < 0.045 and
        abs(electron.dz) < 0.2
    ):
        self.out.pass_tag[0] = True

        if (
            tau.pt > 20 and
            abs(tau.eta) < 2.3 and
            tau.idDeepTau2018v2p5VSjet >= self.tauwp and
            tau.idDeepTau2018v2p5VSe >= 6 and
            tau.idDeepTau2018v2p5VSmu >= 4 and
            tau.decayMode in [0, 1, 10, 11] and
            abs(tau.charge) == 1 and
            tau.DeltaR(electron) >= 0.5
        ):
            self.out.pass_probe[0] = True

    btag_veto = False
    btagThreshold = 0.9
    if btagThreshold > 0:
      for i, jet in enumerate(Collection(event, 'Jet')):
        if (electron.DeltaR(jet) > 0.5) and (tau.DeltaR(jet) > 0.5) and (jet.pt > 20) and (abs(jet.eta) < 2.4) and (jet.btagDeepFlavB > btagThreshold):
          btag_veto = True
          break

    if btag_veto:
      return False
    self.out.cutflow.fill('btag_veto')

    #  TRIGOBJ   


    self.out.trig_match_DeepTau_ETau[0]         = False

    self.out.trig_match_PNet_ETau_Loose[0]      = False
    self.out.trig_match_PNet_ETau_Medium[0]     = False
    self.out.trig_match_PNet_ETau_Tight[0]      = False

    self.out.trig_obj_15[0] = False
    self.out.trig_obj_11[0] = False
    self.out.dR_ele[0] = False

    for i in range(event.nTrigObj):
        if event.TrigObj_id[i] == 11:
            bits = event.TrigObj_filterBits[i]
            self.out.trig_obj_11[0] = True
            dR_ele = deltaR(event.TrigObj_eta[i], electron.eta, event.TrigObj_phi[i], electron.phi)
            if dR_ele < 0.5 and has_filter_bit(bits, 1):
                self.out.dR_ele[0] = False
                self.out.trig_match_single_electron[0] = True

    for i in range(event.nTrigObj):
        if event.TrigObj_id[i] != 15:
            continue

        self.out.trig_obj_15[0] = True

        dR = deltaR(event.TrigObj_eta[i], tau.eta, event.TrigObj_phi[i], tau.phi)
        if dR >= 0.5:
            continue

        pt   = event.TrigObj_pt[i]
        eta  = event.TrigObj_eta[i]
        bits = event.TrigObj_filterBits[i]
        l1pt = event.TrigObj_l1pt[i]  if hasattr(event, "TrigObj_l1pt")  else 0
        l1iso= event.TrigObj_l1iso[i] if hasattr(event, "TrigObj_l1iso") else 0

        # DeepTau trigger bits
        if has_filter_bit(bits, 3) and has_filter_bit(bits, 12):
          if pt > 30 and abs(eta) < 2.1:
              self.out.trig_match_DeepTau_ETau[0] = True

        if self.year in [2024,2025]:
          if pt > 27 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 12):
            if has_filter_bit(bits, 0):
                self.out.trig_match_PNet_ETau_Loose[0] = True
            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_ETau_Medium[0] = True
            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_ETau_Tight[0] = True

        self.out.trig_match_single_electron[0] = False
        for i in range(event.nTrigObj):
          bits = event.TrigObj_filterBits[i]
          if event.TrigObj_id[i] == 11:  
              self.out.trig_obj_11[0] = True
          dR_ele = deltaR(event.TrigObj_eta[i], electron.eta, event.TrigObj_phi[i], electron.phi)
          if dR_ele < 0.5:
            self.out.dR_ele[0] = False    
          if dR_ele < 0.5 and event.TrigObj_id[i] == 11 and has_filter_bit(bits, 1):
            self.out.trig_match_single_electron[0] = True

    
    
    # electron
    self.out.pt_1[0]                       = electron.pt
    self.out.eta_1[0]                      = electron.eta
    self.out.phi_1[0]                      = electron.phi
    self.out.m_1[0]                        = electron.mass
    self.out.y_1[0]                        = electron.tlv.Rapidity()
    self.out.dxy_1[0]                      = electron.dxy
    self.out.dz_1[0]                       = electron.dz
    self.out.q_1[0]                        = electron.charge
    self.out.iso_1[0]                      = electron.pfRelIso03_all
    #self.out.tkRelIso_1[0]                 = electron.tkRelIso
    self.out.mvaNoIso_WP90_1[0]                 = electron.mvaNoIso_WP90
    
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
    if self.year not in [2024,2025]:
        self.out.rawDeepTau2017v2p1VSe_2[0]    = tau.rawDeepTau2017v2p1VSe
        self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau.rawDeepTau2017v2p1VSmu
        self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau.rawDeepTau2017v2p1VSjet
    
    self.out.rawDeepTau2018v2p5VSe_2[0]    = tau.rawDeepTau2018v2p5VSe
    self.out.rawDeepTau2018v2p5VSmu_2[0]   = tau.rawDeepTau2018v2p5VSmu
    self.out.rawDeepTau2018v2p5VSjet_2[0]  = tau.rawDeepTau2018v2p5VSjet

    self.out.idDecayMode_2[0]              = tau.idDecayMode
    self.out.idDecayModeNewDMs_2[0]        = tau.idDecayModeNewDMs
    if self.year not in [2024,2025]:
        self.out.idDeepTau2017v2p1VSe_2[0]     = tau.idDeepTau2017v2p1VSe
        self.out.idDeepTau2017v2p1VSmu_2[0]    = tau.idDeepTau2017v2p1VSmu
        self.out.idDeepTau2017v2p1VSjet_2[0]   = tau.idDeepTau2017v2p1VSjet

    self.out.idDeepTau2018v2p5VSe_2[0]     = tau.idDeepTau2018v2p5VSe
    self.out.idDeepTau2018v2p5VSmu_2[0]    = tau.idDeepTau2018v2p5VSmu
    self.out.idDeepTau2018v2p5VSjet_2[0]   = tau.idDeepTau2018v2p5VSjet

    self.out.PV_npvsGood[0] = event.PV_npvsGood
    self.out.HLT_Ele30_WPTight_Gsf[0] = event.HLT_Ele30_WPTight_Gsf if hasattr(event, "HLT_Ele30_WPTight_Gsf") else 0

    # PNet trigger paths
    if self.year in [2024, 2025]:
      self.out.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Loose_eta2p3_CrossL1[0] = (
          event.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Loose_eta2p3_CrossL1
          if hasattr(event, "HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Loose_eta2p3_CrossL1") else 0
      )
      self.out.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Medium_eta2p3_CrossL1[0] = (
          event.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Medium_eta2p3_CrossL1
          if hasattr(event, "HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Medium_eta2p3_CrossL1") else 0
      )
      self.out.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Tight_eta2p3_CrossL1[0] = (
          event.HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Tight_eta2p3_CrossL1
          if hasattr(event, "HLT_Ele24_eta2p1_WPTight_Gsf_PNetTauhPFJet30_Tight_eta2p3_CrossL1") else 0
      )

    # DeepTau trigger paths
    if self.year != 2025:
        self.out.HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1[0] = (
            event.HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1
            if hasattr(event, "HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1") else 0
        )
    else:
        self.out.HLT_Ele24_eta2p1_WPTight_Gsf_LooseDeepTauPFTauHPS30_eta2p1_CrossL1[0] = 0

    #L1_pass/fail trigger paths
    # self.out.L1_etau[0]        = (
    #     getattr(event, "L1_LooseIsoEG22er2p1_IsoTau26er2p1_dR_Min0p3", 0) or
    #     getattr(event, "L1_LooseIsoEG22er2p1_Tau70er2p1_dR_Min0p3", 0) or
    #     getattr(event, "L1_LooseIsoEG24er2p1_IsoTau27er2p1_dR_Min0p3", 0)
    # )


    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0]     = electron.genPartFlav
      self.out.genmatch_2[0]     = tau.genPartFlav
      pt, eta, phi, status       = matchgenvistau(event,tau)
      self.out.genvistaupt_2[0]  = pt
      self.out.genvistaueta_2[0] = eta
      self.out.genvistauphi_2[0] = phi
      self.out.gendm_2[0]        = status
      # if self.dozpt:
      #   self.out.mutaufilter[0]  = filtermutau(event)
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,electron,tau)

    if self.ismc:
      self.out.jpt_match_2[0], self.out.jpt_genmatch_2[0] = matchtaujet(event,tau,self.ismc)
    else:
      self.out.jpt_match_2[0] = matchtaujet(event,tau,self.ismc)[0]
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if electron.pfRelIso03_all<0.50 and tau.idDeepTau2018v2p5VSjet>=2:
         self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      

      # electron WEIGHTS
      if self.year==2024:
        self.out.trigweight[0]          = 1.
        self.out.idisoweight_1[0]       = 1.
      else:
        self.out.trigweight[0]          = self.eleSFs.getTriggerSF(electron.pt,electron.eta) # assume leading electron was triggered on
        self.out.idisoweight_1[0]       = self.eleSFs.getIdIsoSF(electron.pt,electron.eta, electron.phi)

      
      #print("eta: ", electron.eta)
      #print("pt: ",  electron.pt)
      ##print("idiso sf: ", self.out.idisoweight_1[0])
      ##print("trig sf: ", self.out.trigweight[0])
      #print("===>>> ID&ISO SF")
      #print("sf wo abs: ", self.muSFs.getIdIsoSF(electron.pt,electron.eta))
      #print("sf w abs: ", self.muSFs.getIdIsoSF(electron.pt,abs(electron.eta)))
      #print("===>>> TRIG SF")
      #print("sf wo abs: ", self.muSFs.getTriggerSF(electron.pt,electron.eta))
      #print("sf w abs: ", self.muSFs.getTriggerSF(electron.pt,abs(electron.eta)))

      # DEFAULTS
      self.out.idweight_2[0]          = 1.
      # self.out.idweight_dm_2[0]       = 1.
      # self.out.idweight_medium_2[0]   = 1.
      
      self.out.ltfweight_2[0]         = 1.
      # if self.dosys:
      #   self.out.idweightUp_2[0]      = 1.
      #   self.out.idweightDown_2[0]    = 1.
      #   self.out.idweightUp_dm_2[0]   = 1.
      #   self.out.idweightDown_dm_2[0] = 1.
      #   self.out.ltfweightUp_2[0]     = 1.
      #   self.out.ltfweightDown_2[0]   = 1.
      
      # WEIGHTS

      self.out.weight[0]              = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0] #*self.out.idisoweight_2[0]
    elif self.isembed:
      ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
      self.out.genweight[0]           = event.genWeight
      self.out.trackweight[0]         = 0.975 if tau.decayMode==0 else 1.0247 if tau.decayMode==1 else 0.927 if tau.decayMode==10 else 0.974 if tau.decayMode==11 else 1.0
    
    if not self.ismc:
      self.out.weight[0] = 1
    if electron.charge == tau.charge:
      self.out.weight[0] *= -1 
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,electron,tau,met,met_vars)
    
    
    self.out.fill()
    return True
    