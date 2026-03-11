# Author: Andrea Cardini (Oct 2023)
# Description: Simple module to pre-select mutau events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.Tau_trig_SF_studies.TreeProducerMuTau_trig import *
from TauFW.PicoProducer.analysis.Tau_trig_SF_studies.ModuleTauPair_trig import *
from TauFW.PicoProducer.analysis.utils import LeptonTauPair, loosestIso, idIso, matchgenvistau, matchtaujet, filtermutau
from TauFW.PicoProducer.corrections.MuonSFs import *
#from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool
import ROOT
from ROOT import TVector2, TMath

def deltaR(eta1, eta2, phi1, phi2):
    deta = eta1 - eta2
    dphi = TVector2.Phi_mpi_pi(phi1 - phi2)
    return TMath.Sqrt(deta*deta + dphi*dphi)

def has_filter_bit(bits, bit):
    return (bits & (1 << bit)) != 0

class ModuleMuTau_trig(ModuleTauPair_trig):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mutau'
    super(ModuleMuTau_trig,self).__init__(fname,**kwargs)
    self.out = TreeProducerMuTau_trig(fname,self)
    print("=====> ERA: ", self.era)
    print("=====> YEAR: ", self.year) 
    # TRIGGERS
    if self.year==2016:
      self.trigger    = lambda e: e.HLT_IsoMu22 or e.HLT_IsoMu22_eta2p1 or e.HLT_IsoTkMu22 or e.HLT_IsoTkMu22_eta2p1 #or e.HLT_IsoMu19_eta2p1_LooseIsoPFTau20_SingleL1
      self.muonCutPt  = lambda e: 23
      self.muonCutEta = lambda e: 2.4 if e.HLT_IsoMu22 or e.HLT_IsoTkMu22 else 2.1
    elif self.year==2017:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muonCutPt  = lambda e: 25 if e.HLT_IsoMu24 else 28
      self.muonCutEta = lambda e: 2.4
    elif self.year==2018:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27#e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muonCutPt  = lambda e: 25
      self.muonCutEta = lambda e: 2.4
    elif self.year==2022 or self.year==2023:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27#e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
      self.muonCutPt  = lambda e: 26
      self.muonCutEta = lambda e: 2.4
    elif self.year==2024 or self.year == 2025 or self.year == 2026:
    #   self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27#e.HLT_IsoMu27 #or e.HLT_IsoMu20_eta2p1_LooseChargedIsoPFTau27_eta2p1_CrossL1
    #   self.trigger    = lambda e: True
      self.muonCutPt  = lambda e: 24
      self.muonCutEta = lambda e: 2.1    
    else:
      self.trigger    = lambda e: e.HLT_IsoMu24 or e.HLT_IsoMu27
      self.muonCutPt  = lambda e: 26
      self.muonCutEta = lambda e: 2.4
    self.tauCutPt     = 20
    self.tauCutEta    = 2.5 # 2.3 DeepTau2p1 and 2.5 for DeepTau2p5

    
    # CORRECTIONS
    if self.ismc:
      if self.year==2024 or self.year == 2025 or self.year == 2026:
        self.muSFs  = 1
      else:
        self.muSFs   = MuonSFs(era=self.era,verb=self.verbosity) # muon id/iso/trigger SFs
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('pair',         "pair"                       )
    #self.out.cutflow.addcut('muonveto',     "muon veto"                  )
    #self.out.cutflow.addcut('elecveto',     "electron veto"              )
    self.out.cutflow.addcut('lepvetoes',     "lep vetoes"              )
    self.out.cutflow.addcut('jetvetoes',     "jet vetoes"              )
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
    super(ModuleMuTau_trig,self).beginJob()
    print(">>> %-12s = %s"%('tauwp',      self.tauwp))
    print(">>> %-12s = %s"%('muonCutPt',  self.muonCutPt))
    print(">>> %-12s = %s"%('muonCutEta', self.muonCutEta))
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
    if self.year not in [2024,2025]:
        if not self.trigger(event):
            return False
        self.out.cutflow.fill('trig')    
    
    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<self.muonCutPt(event): continue
      if abs(muon.eta)>self.muonCutEta(event): continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.1: continue
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
    best_pair = None
    min_muon_iso = float('inf')
    max_tau_pt = -1.0

    for muon in muons:
        for tau in taus:
            if tau.DeltaR(muon) <= 0.5:
                continue
            iso = muon.pfRelIso04_all
            pt  = tau.pt
            if (
                iso < min_muon_iso or
                (iso == min_muon_iso and pt > max_tau_pt)
            ):
                best_pair = (muon, tau)
                min_muon_iso = iso
                max_tau_pt = pt

    if best_pair is None:
        return False

    muon, tau = best_pair
    muon.tlv = muon.p4()
    tau.tlv  = tau.p4()
    genmatch  = -1 if self.isdata else tau.genPartFlav
    m_vis = (muon.tlv + tau.tlv).M()
    if m_vis < 40 or m_vis > 80:
      return False

    puppimet_vec = ROOT.TVector2(event.PuppiMET_pt, event.PuppiMET_phi)
    mu_vec = ROOT.TVector2(muon.pt, muon.phi)
    mT = TMath.Sqrt(2 * muon.pt * event.PuppiMET_pt * (1 - TMath.Cos(mu_vec.DeltaPhi(puppimet_vec))))
    if mT >= 30:
      return False

    self.out.cutflow.fill('pair')

    for ele in Collection(event, 'Electron'):
        if ele.pt > 10 and abs(ele.eta) < 2.5 and ele.mvaIso > 0.5:
            return False
    # self.out.cutflow.fill('eveto')

    signal_muon_index = muon._index if hasattr(muon, '_index') else -1
    for i, other_muon in enumerate(Collection(event, 'Muon')):
        if other_muon.pt > 10 and abs(other_muon.eta) < 2.4 and other_muon.looseId:
            if i != signal_muon_index:
                return False
    # self.out.cutflow.fill('muveto')
    
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ ],[muon],[tau],self.channel,era=self.era)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[ ],[muon],[ ],self.channel,era=self.era)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    

    #cutflow on veto
    if self.out.lepton_vetoes[0] and self.out.lepton_vetoes_notau[0]: return False
    self.out.cutflow.fill('lepvetoes')

    if self.jetveto(event): return False
    self.out.cutflow.fill('jetvetoes')
   
 
    # EVENT
    self.fillEventBranches(event)
    if self.year == 2024:
      # if not self.ismc:        
      #   self.out.Flag_METFilters[0] = event.Flag_METFilters
      # if self.ismc:        
      self.out.Flag_METFilters[0] = True

    # self.out.Flag_goodVertices[0] = event.Flag_goodVertices
    # self.out.Flag_globalSuperTightHalo2016Filter[0] = event.Flag_globalSuperTightHalo2016Filter
    # self.out.Flag_HBHENoiseFilter[0] = event.Flag_HBHENoiseFilter
    # self.out.Flag_HBHENoiseIsoFilter[0] = event.Flag_HBHENoiseIsoFilter
    # if not self.ismc:
    #     self.out.Flag_eeBadScFilter[0] = event.Flag_eeBadScFilter
    # self.out.Flag_EcalDeadCellTriggerPrimitiveFilter[0] = event.Flag_EcalDeadCellTriggerPrimitiveFilter
    # self.out.Flag_BadPFMuonFilter[0] = event.Flag_BadPFMuonFilter
    # self.out.Flag_BadPFMuonDzFilter[0] = event.Flag_BadPFMuonDzFilter
    # self.out.Flag_ecalBadCalibFilter[0] = event.Flag_ecalBadCalibFilter    

    self.out.Flag_goodVertices[0]                   = getattr(event, "Flag_goodVertices", True)
    self.out.Flag_globalSuperTightHalo2016Filter[0] = getattr(event, "Flag_globalSuperTightHalo2016Filter", True)
    self.out.Flag_HBHENoiseFilter[0]                = getattr(event, "Flag_HBHENoiseFilter", True)
    self.out.Flag_HBHENoiseIsoFilter[0]             = getattr(event, "Flag_HBHENoiseIsoFilter", True)
    if not self.ismc:
        self.out.Flag_eeBadScFilter[0]              = getattr(event, "Flag_eeBadScFilter", True)
    self.out.Flag_EcalDeadCellTriggerPrimitiveFilter[0] = getattr(event, "Flag_EcalDeadCellTriggerPrimitiveFilter", True)
    self.out.Flag_BadPFMuonFilter[0]                = getattr(event, "Flag_BadPFMuonFilter", True)
    self.out.Flag_BadPFMuonDzFilter[0]              = getattr(event, "Flag_BadPFMuonDzFilter", True)
    self.out.Flag_ecalBadCalibFilter[0]             = getattr(event, "Flag_ecalBadCalibFilter", True)

    self.out.pass_tag[0] = False
    self.out.pass_probe[0] = False
    if (
        muon.pt > 24 and
        abs(muon.eta) < 2.1 and
        muon.mediumId and
        muon.pfRelIso04_all < 0.1 and
        abs(muon.dxy) < 0.045 and
        abs(muon.dz) < 0.2
    ):
        self.out.pass_tag[0] = True

        if (
            tau.pt > 20 and
            abs(tau.eta) < 2.3 and
            tau.idDeepTau2018v2p5VSjet >= self.tauwp and
            tau.idDeepTau2018v2p5VSe >= 2 and
            tau.idDeepTau2018v2p5VSmu >= 4 and
            tau.decayMode in [0, 1, 10, 11] and
            abs(tau.charge) == 1 and
            tau.DeltaR(muon) >= 0.5
        ):
            self.out.pass_probe[0] = True

    #  TRIGOBJ   
    self.out.trig_match_DeepTau_MuTau[0]        = False
    self.out.trig_match_DeepTau_DiTau[0]        = False
    self.out.trig_match_DeepTau_DiTauJet[0]     = False
    self.out.trig_match_DeepTau_ETau[0]         = False
    self.out.trig_match_DeepTau_VBFSingleTau[0] = False
    self.out.trig_match_DeepTau_VBFDiTau[0]     = False

    self.out.trig_match_PNet_SingleTau_Loose[0]  = False
    self.out.trig_match_PNet_SingleTau_Medium[0] = False
    self.out.trig_match_PNet_SingleTau_Tight[0]  = False
    self.out.trig_match_PNet_MuTau_Loose[0]     = False
    self.out.trig_match_PNet_MuTau_Medium[0]    = False
    self.out.trig_match_PNet_MuTau_Tight[0]     = False
    self.out.trig_match_PNet_DiTau_Flat[0]      = False
    self.out.trig_match_PNet_DiTau_Loose[0]     = False
    self.out.trig_match_PNet_DiTau_Medium[0]    = False
    self.out.trig_match_PNet_DiTau_Tight[0]     = False
    self.out.trig_match_PNet_DiTauJet[0]        = False
    self.out.trig_match_PNet_ETau_Loose[0]      = False
    self.out.trig_match_PNet_ETau_Medium[0]     = False
    self.out.trig_match_PNet_ETau_Tight[0]      = False
    self.out.trig_match_PNet_VBFSingleTau[0]    = False
    self.out.trig_match_PNet_VBFDiTau[0]        = False
    self.out.trig_match_PNet_ETau_Loose_2025E[0]  = False
    self.out.trig_match_PNet_ETau_Medium_2025E[0] = False
    self.out.trig_match_PNet_ETau_Tight_2025E[0]  = False

    self.out.trig_obj_15[0] = False
    self.out.trig_obj_13[0] = False
    self.out.dR_mu[0] = False

    self.out.pass_L2NN[0] = False
    self.out.pass_PNet_Tauh[0] = False
    self.out.pass_MuTau_overlap[0] = False 

    self.out.trig_match_single_muon[0] = False
    for i in range(event.nTrigObj):
      bits = event.TrigObj_filterBits[i]
      if event.TrigObj_id[i] == 13:  
          self.out.trig_obj_13[0] = True
      dR_mu = deltaR(event.TrigObj_eta[i], muon.eta, event.TrigObj_phi[i], muon.phi)
      if dR_mu < 0.5:
        self.out.dR_mu[0] = (dR_mu < 0.5)    
      if dR_mu < 0.5 and event.TrigObj_id[i] == 13 and has_filter_bit(bits, 1) and (has_filter_bit(bits, 3) or has_filter_bit(bits, 6)):
        self.out.trig_match_single_muon[0] = True

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

        if has_filter_bit(bits, 31):
            self.out.pass_L2NN[0] = True
        if has_filter_bit(bits, 32):
            self.out.pass_PNet_Tauh[0] = True
        if has_filter_bit(bits, 33):
            self.out.pass_MuTau_overlap[0] = True

        # DeepTau trigger bits
        if has_filter_bit(bits, 3) and has_filter_bit(bits, 13):
            if pt > 27 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_MuTau[0] = True

        if has_filter_bit(bits, 3) and has_filter_bit(bits, 23):
            if pt > 35 and l1pt > 34 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_DiTau[0] = True

        if has_filter_bit(bits, 3) and has_filter_bit(bits, 20):
            if pt > 30 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_DiTauJet[0] = True

        if has_filter_bit(bits, 3) and has_filter_bit(bits, 13):
            if pt > 27 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_ETau[0] = True

        if has_filter_bit(bits, 3) and has_filter_bit(bits, 19):
            if pt > 45 and l1pt > 45 and l1iso > 0 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_VBFSingleTau[0] = True

        if has_filter_bit(bits, 3) and has_filter_bit(bits, 25):
            if pt > 20 and abs(eta) < 2.1:
                self.out.trig_match_DeepTau_VBFDiTau[0] = True

        # Pnet trigger bits

        # SingleTau Monitoring (PNet)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Loose_L2NN_eta2p3_CrossL1 (+Medium, Tight)
        # bits: wp (0/1/2), 4 (PNet), 26 (SingleTau Monitoring)

        if (pt > 130 and l1pt > 130 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 26)):
            if has_filter_bit(bits, 0):
                self.out.trig_match_PNet_SingleTau_Loose[0] = True

            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_SingleTau_Medium[0] = True

            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_SingleTau_Tight[0] = True

        # MuTau (PNet)
        # HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1 (+Medium, Tight)
        # bits: wp (0/1/2), 4 (PNet), 13 (MuTau)

        if pt > 27 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 13):
            if has_filter_bit(bits, 0):
                self.out.trig_match_PNet_MuTau_Loose[0] = True
            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_MuTau_Medium[0] = True
            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_MuTau_Tight[0] = True
            
        # DiTau Monitoring (PNet)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1 (+Tight)
        # bits: wp (1/2), 4 (PNet), 23 (DiTau Monitoring)

        if pt > 30 and l1pt > 34 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 23):
            self.out.trig_match_PNet_DiTau_Flat[0] = True
            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_DiTau_Medium[0] = True

            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_DiTau_Tight[0] = True

        # DiTau+Jet Monitoring (PNet)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1 (+PFJet60, PFJet75)
        # bits: 4 (PNet), 20 (DiTau+Jet Monitoring)

        if pt > 26 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 20):
            self.out.trig_match_PNet_DiTauJet[0] = True

        # ETau (PNet) (Bugged Trigger so using MuTau bit)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Loose_eta2p3_CrossL1_ETau_Monitoring (+Medium, Tight)
        # bits: wp (0/1/2), 4 (PNet), 13 (MuTau inside filter)

        if pt > 27 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 13):
            if has_filter_bit(bits, 0):
                self.out.trig_match_PNet_ETau_Loose[0] = True
            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_ETau_Medium[0] = True
            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_ETau_Tight[0] = True

        # ETau (PNet, 2025E+ MatchL1HLT) (Trigger bit fixed from 2025E)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Loose_eta2p3_CrossL1_ETau_Monitoring (+Medium, Tight)
        # bits: wp (0/1/2), 4 (PNet), 27 (MatchL1HLT)

        if pt > 27 and l1pt > 26 and l1iso > 0 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 27):
            if has_filter_bit(bits, 0):
                self.out.trig_match_PNet_ETau_Loose_2025E[0] = True
            if has_filter_bit(bits, 1):
                self.out.trig_match_PNet_ETau_Medium_2025E[0] = True
            if has_filter_bit(bits, 2):
                self.out.trig_match_PNet_ETau_Tight_2025E[0] = True

        # VBF SingleTau Monitoring (PNet)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1
        # bits: 4 (PNet), 19 (VBF SingleTau Monitoring)

        if pt > 45 and l1pt > 45 and l1iso > 0 and abs(eta) < 2.3 and has_filter_bit(bits, 4) and has_filter_bit(bits, 19):
            self.out.trig_match_PNet_VBFSingleTau[0] = True

        # VBF DiTau Monitoring (PNet)
        # HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1
        # bits: 4 (PNet), 25 (VBF DiTau Monitoring)

        if pt > 20 and abs(eta) < 2.2 and has_filter_bit(bits, 4) and has_filter_bit(bits, 25):
            self.out.trig_match_PNet_VBFDiTau[0] = True

    self.out.L1_mutau[0]        = False
    self.out.L1_etau[0]         = False
    self.out.L1_ditau[0]        = False
    self.out.L1_ditaujet[0]     = False
    self.out.L1_singletau[0]    = False
    self.out.L1_vbfsingletau[0] = False
    self.out.L1_vbfditau[0]     = False

    for i in range(event.nTrigObj):

        l1pt  = event.TrigObj_l1pt[i]  if hasattr(event,"TrigObj_l1pt") else 0
        l1iso = event.TrigObj_l1iso[i] if hasattr(event,"TrigObj_l1iso") else 0

        has_mutau_seed = (
            getattr(event,"L1_Mu18er2p1_Tau24er2p1",0) or
            getattr(event,"L1_Mu18er2p1_Tau26er2p1",0)
        )

        self.out.L1_mutau[0] |= has_mutau_seed

        self.out.L1_etau[0] |= (
            has_mutau_seed and l1pt > 26 and l1iso > 0
        )

        self.out.L1_ditau[0] |= (
            (getattr(event,"L1_Mu22er2p1_IsoTau32er2p1",0) or
            getattr(event,"L1_Mu22er2p1_IsoTau34er2p1",0) or
            getattr(event,"L1_Mu22er2p1_Tau70er2p1",0))
            and l1pt > 34
        )

        l1pt_cut = 26 if self.year==2024 else 23
        self.out.L1_ditaujet[0] |= (
            (getattr(event,"L1_Mu18er2p1_Tau24er2p1",0) or
            getattr(event,"L1_Mu18er2p1_Tau26er2p1",0) or
            getattr(event,"L1_Mu18er2p1_Tau26er2p1_Jet55",0) or
            getattr(event,"L1_Mu18er2p1_Tau26er2p1_Jet70",0))
            and l1pt > l1pt_cut and l1iso > 0
        )

        self.out.L1_singletau[0] |= (
            getattr(event,"L1_Mu22er2p1_IsoTau40er2p1",0) and l1pt > 130
        )

        self.out.L1_vbfsingletau[0] |= (
            (getattr(event,"L1_Mu22er2p1_IsoTau32er2p1",0) or
            getattr(event,"L1_Mu22er2p1_IsoTau34er2p1",0) or
            getattr(event,"L1_Mu22er2p1_Tau70er2p1",0))
            and l1pt > 45 and l1iso > 0
        )

        self.out.L1_vbfditau[0] |= getattr(event,"L1_SingleMu22",0)

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
    #self.out.tkRelIso_1[0]                 = muon.tkRelIso
    self.out.idMedium_1[0]                 = muon.mediumId
    self.out.idTight_1[0]                  = muon.tightId
    self.out.idHighPt_1[0]                 = muon.highPtId
    
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
    self.out.HLT_IsoMu24[0]        = event.HLT_IsoMu24 if hasattr(event, "HLT_IsoMu24") else 0
    self.out.HLT_IsoMu24_eta2p1[0] = event.HLT_IsoMu24_eta2p1 if hasattr(event, "HLT_IsoMu24_eta2p1") else 0

    #### CUSTOM DITAU TRIGGERS
    # try:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1[0] = \
    #         event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1
    # except RuntimeError:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1[0] = 0


    # try:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1[0] = \
    #         event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1
    # except RuntimeError:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1[0] = 0


    # try:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VTight_L2NN_eta2p3_CrossL1[0] = \
    #         event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VTight_L2NN_eta2p3_CrossL1
    # except RuntimeError:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VTight_L2NN_eta2p3_CrossL1[0] = 0


    # try:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VVTight_L2NN_eta2p3_CrossL1[0] = \
    #         event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VVTight_L2NN_eta2p3_CrossL1
    # except RuntimeError:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_VVTight_L2NN_eta2p3_CrossL1[0] = 0


    # try:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Flat_L2NN_eta2p3_CrossL1[0] = \
    #         event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Flat_L2NN_eta2p3_CrossL1
    # except RuntimeError:
    #     self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Flat_L2NN_eta2p3_CrossL1[0] = 0

    # ParticleNet HLT Paths

    # Single Tau Loose
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Loose_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Loose_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Loose_L2NN_eta2p3_CrossL1") else 0
    )

    # Single Tau Medium
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Medium_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Medium_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Medium_L2NN_eta2p3_CrossL1") else 0
    )

    # Single Tau Tight
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Tight_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Tight_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet130_Tight_L2NN_eta2p3_CrossL1") else 0
    )

    # DiTau Medium
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1") else 0
    )

    # DiTau Tight
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_L2NN_eta2p3_CrossL1") else 0
    )

    # DiTau+Jet
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1") else 0
    )

    # DiTau+Jet (PFJet60)
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet60[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet60
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet60") else 0
    )

    # DiTau+Jet (PFJet75)
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet75[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet75
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1_PFJet75") else 0
    )

    # MuTau Loose
    self.out.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1") else 0
    )

    # MuTau Medium
    self.out.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Medium_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Medium_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Medium_eta2p3_CrossL1") else 0
    )

    # MuTau Tight
    self.out.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1") else 0
    )

    # ETau Loose
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Loose_eta2p3_CrossL1_ETau_Monitoring[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Loose_eta2p3_CrossL1_ETau_Monitoring
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Loose_eta2p3_CrossL1_ETau_Monitoring") else 0
    )

    # ETau Medium
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_eta2p3_CrossL1_ETau_Monitoring[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_eta2p3_CrossL1_ETau_Monitoring
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_eta2p3_CrossL1_ETau_Monitoring") else 0
    )

    # ETau Tight
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_eta2p3_CrossL1_ETau_Monitoring[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_eta2p3_CrossL1_ETau_Monitoring
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Tight_eta2p3_CrossL1_ETau_Monitoring") else 0
    )

    # VBF SingleTau
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1") else 0
    )

    # VBF DiTau
    self.out.HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1[0] = (
        event.HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1
        if hasattr(event, "HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1") else 0
    )

    # DeepTau trigger paths
    if self.year != 2025:
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1[0] = (
            event.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1
            if hasattr(event, "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1") else 0
        )
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1[0] = (
            event.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1
            if hasattr(event, "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1") else 0
        )
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1[0] = (
            event.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1
            if hasattr(event, "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1") else 0
        )
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1[0] = (
            event.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1
            if hasattr(event, "HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1") else 0
        )
        self.out.HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1[0] = (
            event.HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1
            if hasattr(event, "HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1") else 0
        )
    else:
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1[0] = 0
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1[0] = 0
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1[0] = 0
        self.out.HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1[0] = 0
        self.out.HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1[0] = 0

    # #L1_pass/fail trigger paths
    # self.out.L1_mutau[0]       = (
    #     getattr(event, "L1_Mu18er2p1_Tau24er2p1", 0) or
    #     getattr(event, "L1_Mu18er2p1_Tau26er2p1", 0)
    # )

    # self.out.L1_etau[0]        = (
    #     getattr(event, "L1_Mu18er2p1_Tau24er2p1", 0) or
    #     getattr(event, "L1_Mu18er2p1_Tau26er2p1", 0)
    # )

    # self.out.L1_ditau[0]       = (
    #     getattr(event, "L1_Mu22er2p1_IsoTau32er2p1", 0) or
    #     getattr(event, "L1_Mu22er2p1_IsoTau34er2p1", 0) or
    #     # getattr(event, "L1_Mu22er2p1_IsoTau36er2p1", 0) or
    #     getattr(event, "L1_Mu22er2p1_Tau70er2p1", 0)
    # )

    # self.out.L1_ditaujet[0]    = (
    #     getattr(event, "L1_Mu18er2p1_Tau24er2p1", 0) or
    #     getattr(event, "L1_Mu18er2p1_Tau26er2p1", 0) or
    #     getattr(event, "L1_Mu18er2p1_Tau26er2p1_Jet55", 0) or
    #     getattr(event, "L1_Mu18er2p1_Tau26er2p1_Jet70", 0)
    # )

    # self.out.L1_singletau[0]   = getattr(event, "L1_Mu22er2p1_IsoTau40er2p1", 0)

    # self.out.L1_vbfsingletau[0] = (
    #     getattr(event, "L1_Mu22er2p1_IsoTau32er2p1", 0) or
    #     getattr(event, "L1_Mu22er2p1_IsoTau34er2p1", 0) or
    #     # getattr(event, "L1_Mu22er2p1_IsoTau36er2p1", 0) or
    #     getattr(event, "L1_Mu22er2p1_Tau70er2p1", 0)
    # )

    # self.out.L1_vbfditau[0]    = getattr(event, "L1_SingleMu22", 0)


    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0]     = muon.genPartFlav
      self.out.genmatch_2[0]     = tau.genPartFlav
      pt, eta, phi, status       = matchgenvistau(event,tau)
      self.out.genvistaupt_2[0]  = pt
      self.out.genvistaueta_2[0] = eta
      self.out.genvistauphi_2[0] = phi
      self.out.gendm_2[0]        = status
      if self.dozpt:
        self.out.mutaufilter[0]  = filtermutau(event)
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,muon,tau)

    if self.ismc:
      self.out.jpt_match_2[0], self.out.jpt_genmatch_2[0] = matchtaujet(event,tau,self.ismc)
    else:
      self.out.jpt_match_2[0] = matchtaujet(event,tau,self.ismc)[0]
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if muon.pfRelIso04_all<0.50 and tau.idDeepTau2018v2p5VSjet>=2:
         self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      

      # MUON WEIGHTS
      if self.year==2024 or self.year == 2025 or self.year == 2026:
        self.out.trigweight[0]          = 1.
        self.out.idisoweight_1[0]       = 1.
      else:
        self.out.trigweight[0]          = self.muSFs.getTriggerSF(muon.pt,muon.eta) # assume leading muon was triggered on
        self.out.idisoweight_1[0]       = self.muSFs.getIdIsoSF(muon.pt,muon.eta)

      
      #print("eta: ", muon.eta)
      #print("pt: ",  muon.pt)
      ##print("idiso sf: ", self.out.idisoweight_1[0])
      ##print("trig sf: ", self.out.trigweight[0])
      #print("===>>> ID&ISO SF")
      #print("sf wo abs: ", self.muSFs.getIdIsoSF(muon.pt,muon.eta))
      #print("sf w abs: ", self.muSFs.getIdIsoSF(muon.pt,abs(muon.eta)))
      #print("===>>> TRIG SF")
      #print("sf wo abs: ", self.muSFs.getTriggerSF(muon.pt,muon.eta))
      #print("sf w abs: ", self.muSFs.getTriggerSF(muon.pt,abs(muon.eta)))

      # DEFAULTS
      self.out.idweight_2[0]          = 1.
      self.out.idweight_dm_2[0]       = 1.
      self.out.idweight_medium_2[0]   = 1.
      
      self.out.ltfweight_2[0]         = 1.
      if self.dosys:
        self.out.idweightUp_2[0]      = 1.
        self.out.idweightDown_2[0]    = 1.
        self.out.idweightUp_dm_2[0]   = 1.
        self.out.idweightDown_dm_2[0] = 1.
        self.out.ltfweightUp_2[0]     = 1.
        self.out.ltfweightDown_2[0]   = 1.
      
      # WEIGHTS

      self.out.weight[0]              = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0] #*self.out.idisoweight_2[0]
    elif self.isembed:
      ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
      self.out.genweight[0]           = event.genWeight
      self.out.trackweight[0]         = 0.975 if tau.decayMode==0 else 1.0247 if tau.decayMode==1 else 0.927 if tau.decayMode==10 else 0.974 if tau.decayMode==11 else 1.0
     
        
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,muon,tau,met,met_vars)
    
    
    self.out.fill()
    return True
    
