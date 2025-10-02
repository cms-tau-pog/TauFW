# Author: Konstantinos Christoforou (Jan 2022)
# Description: Simple module to pre-select mumutau events
# for measuring jet to tau Fake Rate in WJets-enriched region
import sys
import numpy as np
from math import sin, cos, sqrt

from ROOT import TFile, TTree, TH1D
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool, campaigns

from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.corrections.BTagTool import BTagWeightTool, BTagWPs
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.RecoilCorrectionTool import *
from TauFW.PicoProducer.corrections.PileupTool import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import TrigObjMatcher
from TauFW.PicoProducer.analysis.utils import deltaPhi, getmetfilters, correctmet
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool, campaigns

class ModuleMuMETTau(Module):
  
  def __init__(self,fname,**kwargs):
    self.outfile = TFile(fname,'RECREATE')
    self.channel    = kwargs.get('channel',  'none'         ) # channel name
    self.dtype      = kwargs.get('dtype',    'data'         )
    self.ismc       = self.dtype=='mc'
    self.isdata     = self.dtype=='data' or self.dtype=='embed'
    self.isembed    = self.dtype=='embed'
    self.era        = kwargs.get('era',     2017           ) # integer, e.g. 2017, 2018, 2018UL
    self.dotoppt    = kwargs.get('toppt',    'TT' in fname  ) # top pT reweighting
    self.dozpt      = kwargs.get('zpt',      'DY' in fname  ) # Z pT reweighting
    self.verbosity  = kwargs.get('verb',     0              ) # verbosity
    
    tauSFVersion  = { 2016: '2016Legacy', 2017: '2017ReReco', 2018: '2018ReReco' }
    if "2016" in self.era : 
      self.yearForTauSF = 2016
      self.muonTrgPt = 25.0
    elif "2017" in self.era : 
      self.yearForTauSF = 2017
      self.muonTrgPt = 28.0
    elif "2018" in self.era :
      self.yearForTauSF = 2018
      self.muonTrgPt = 25.0
    else :
      "Sanity check error, no 2016/2017/2018 in self.era"
    
    ## For Trigger Matching
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.yearForTauSF))
    jsonfileCorrected = jsonfile.replace("/pileup","") ## for some reason the pileup subfolder is selected as datadir, instead of just the data folder, fixme
    self.trigger   = TrigObjMatcher(jsonfileCorrected,trigger='SingleMuon',isdata=self.isdata)
    
    ## CORRECTIONS
    self.metfilt      = getmetfilters(self.era,self.isdata,verb=self.verbosity)
    if self.ismc:
      self.puTool     = PileupWeightTool(era=self.era,sample=fname,verb=self.verbosity)
      if self.dozpt:
        self.zptTool  = ZptCorrectionTool(era=self.era)
      self.muSFs      = MuonSFs(era=self.era,verb=self.verbosity) # muon id/iso/trigger SFs
      self.tesTool    = TauESTool(tauSFVersion[self.yearForTauSF])  # real tau energy scale corrections
      self.tauSFsT_dm = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSjet','Tight', dm=True)
      self.tauSFsT    = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSjet','Tight')
      self.tauSFsM    = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSjet','Medium')
      self.tauSFsVVVL = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSjet','VVVLoose')      
      self.etfSFs     = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSe',  'Medium')
      self.mtfSFs     = TauIDSFTool(tauSFVersion[self.yearForTauSF],'DeepTau2017v2p1VSmu', 'Tight')
    ## after opening the root files for muonSF and tauSF, something is getting confused, so you should reopen
    ## your output file in order to store your trees/branches
    self.outfile.cd()

    self.jetCutPt   = 20.0
    self.bjetCutEta = 2.4 if self.era==2016 else 2.5
    self.deepjet_wp = BTagWPs('DeepJet',era=self.era)

  def beginJob(self):
    """Prepare output analysis tree and cutflow histogram."""
    
    # CUTFLOW HISTOGRAM
    self.cutflow     = TH1D('cutflow','cutflow',25,0,25)
    self.cut_none    = 0
    self.cut_trig    = 1
    self.cut_muon    = 2
    self.cut_fake    = 3
    self.cut_tau     = 4
    self.cut_pair    = 5
    self.cut_loosemu = 6
    self.cut_elecveto = 7
    self.cut_weight  = 16 ## needed for sumbinw
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_none,      "no cut"    )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_trig,      "trigger"   )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_muon,      "muon"      )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_fake,      "fake cand" )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_tau,       "tau"       )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_pair,      "pair"      )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_loosemu,   "loose mu"  )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_elecveto,  "e veto"    )
    self.cutflow.GetXaxis().SetBinLabel(1+self.cut_weight, "no cut, weighted" )

    # TREE
    self.tree          = TTree('tree','tree')
    self.evt           = np.zeros(1,dtype='i')
    self.lumi          = np.zeros(1,dtype='i')
    self.npu           = np.zeros(1,dtype='i')  
    self.npu_true      = np.zeros(1,dtype='i')  
    self.NUP           = np.zeros(1,dtype='i')  
    self.metfilter     = np.zeros(1,dtype='?')
    self.genweight     = np.zeros(1,dtype='f')
    self.puweight      = np.zeros(1,dtype='f')
    self.zptweight     = np.zeros(1,dtype='f')
    self.m_moth        = np.zeros(1,dtype='f')
    self.pt_moth       = np.zeros(1,dtype='f') 
    self.ttptweight    = np.zeros(1,dtype='f')
    self.pt_moth1      = np.zeros(1,dtype='f')
    self.trigweight    = np.zeros(1,dtype='f')
    self.idisoweight_1 = np.zeros(1,dtype='f')
    self.idweightTdm_tau  = np.zeros(1,dtype='f')
    self.idweightT_tau    = np.zeros(1,dtype='f')
    self.idweightM_tau    = np.zeros(1,dtype='f')
    self.idweightVVVL_tau = np.zeros(1,dtype='f')
    self.ltfweight_tau    = np.zeros(1,dtype='f')
    self.pt_mu0   = np.zeros(1,dtype='f')
    self.eta_mu0  = np.zeros(1,dtype='f')
    self.q_mu0    = np.zeros(1,dtype='i')
    self.id_mu0   = np.zeros(1,dtype='?')
    self.iso_mu0  = np.zeros(1,dtype='f')
    self.pt_tau   = np.zeros(1,dtype='f')
    self.eta_tau  = np.zeros(1,dtype='f')
    self.q_tau    = np.zeros(1,dtype='i')
    self.id_tau   = np.zeros(1,dtype='i')
    self.iso_tau  = np.zeros(1,dtype='f')
    ## Jet to tau FR
    self.JetPt              = np.zeros(1,dtype='f')
    self.JetEta             = np.zeros(1,dtype='f')
    self.TauIsGenuine       = np.zeros(1,dtype='?')
    self.TauPt              = np.zeros(1,dtype='f')
    self.TauEta             = np.zeros(1,dtype='f')
    self.TauDM              = np.zeros(1,dtype='i')
    self.TauIdVSe           = np.zeros(1,dtype='i')
    self.TauIdVSmu          = np.zeros(1,dtype='i')
    self.JetN               = np.zeros(1,dtype='i')
    self.MET                = np.zeros(1,dtype='f')
    self.HT                 = np.zeros(1,dtype='f')
    self.LT                 = np.zeros(1,dtype='f')
    self.ST                 = np.zeros(1,dtype='f')
    self.LeptonOnePt        = np.zeros(1,dtype='f')
    self.LeptonMETTMass     = np.zeros(1,dtype='f')
    self.LeptonMETDeltaPhi  = np.zeros(1,dtype='f')

    self.tree.Branch('evt',          self.evt,           'evt/I'          )          
    self.tree.Branch('lumi',         self.lumi,          'lumi/F'         )
    self.tree.Branch('npu',          self.npu,           'npu/I'          )## number of in-time pu interactions added (getPU_NumInteractions -> nPU)
    self.tree.Branch('npu_true',     self.npu_true,      'npu_true/I'     )## true mean number of Poisson distribution (getTrueNumInteractions -> nTrueInt)
    self.tree.Branch('NUP',          self.NUP,           'NUP/I'          )## number of partons for stitching (LHE_Njets)
    self.tree.Branch('metfilter',    self.metfilter,     'metfilter/O'    )   
    self.tree.Branch('genweight',    self.genweight,     'genweight/F'    )          
    self.tree.Branch('puweight',     self.puweight,      'puweight/F'     )          
    self.tree.Branch('zptweight',    self.zptweight,     'zptweight/F'    ) 
    self.tree.Branch('m_moth',       self.m_moth,        'm_moth/F'       )
    self.tree.Branch('pt_moth',      self.pt_moth,       'pt_moth/F'      )      
    self.tree.Branch('ttptweight',   self.ttptweight,    'ttptweight/F'   )
    self.tree.Branch('pt_moth1',     self.pt_moth1,      'pt_moth1/F'     )       
    self.tree.Branch('trigweight',   self.trigweight,    'trigweight/F'   )
    self.tree.Branch('idisoweight_1',self.idisoweight_1, 'idisoweight_1/F')
    self.tree.Branch('idweightTdm_tau',  self.idweightTdm_tau,  'idweightTdm_tau/F'  )
    self.tree.Branch('idweightT_tau',    self.idweightT_tau,    'idweightT_tau/F'    )
    self.tree.Branch('idweightM_tau',    self.idweightM_tau,    'idweightM_tau/F'    )
    self.tree.Branch('idweightVVVL_tau', self.idweightVVVL_tau, 'idweightVVVL_tau/F' )
    self.tree.Branch('ltfweight_tau',    self.ltfweight_tau,    'ltfweight_tau/F'    )
    self.tree.Branch('pt_mu0',   self.pt_mu0,  'pt_mu0/F' )
    self.tree.Branch('eta_mu0',  self.eta_mu0, 'eta_mu0/F')
    self.tree.Branch('q_mu0',    self.q_mu0,   'q_mu0/I'  )
    self.tree.Branch('id_mu0',   self.id_mu0,  'id_mu0/O' )
    self.tree.Branch('iso_mu0',  self.iso_mu0, 'iso_mu0/F')
    self.tree.Branch('pt_tau',   self.pt_tau,  'pt_tau/F' )
    self.tree.Branch('eta_tau',  self.eta_tau, 'eta_tau/F')
    self.tree.Branch('q_tau',    self.q_tau,   'q_tau/I'  )
    self.tree.Branch('id_tau',   self.id_tau,  'id_tau/I' )
    self.tree.Branch('iso_tau',  self.iso_tau, 'iso_tau/F')
    ## Jet to tau FR
    self.tree.Branch("JetPt"           ,  self.JetPt           , "JetPt/F"            )
    self.tree.Branch("JetEta"          ,  self.JetEta          , "JetEta/F"           )
    self.tree.Branch("TauIsGenuine"    ,  self.TauIsGenuine    , "TauIsGenuine/O"     )           
    self.tree.Branch("TauPt"           ,  self.TauPt           , "TauPt/F"            )           
    self.tree.Branch("TauEta"          ,  self.TauEta          , "TauEta/F"           ) 
    self.tree.Branch("TauDM"           ,  self.TauDM           , "TauDM/I"            ) 
    self.tree.Branch("TauIdVSe"        ,  self.TauIdVSe        , "TauIdVSe/I"         )
    self.tree.Branch("TauIdVSmu"       ,  self.TauIdVSmu       , "TauIdVSmu/I"        )   
    self.tree.Branch("JetN"            ,  self.JetN            , "JetN/I"             ) 
    self.tree.Branch("MET"             ,  self.MET             , "MET/F"              ) 
    self.tree.Branch("HT"              ,  self.HT              , "HT/F"               ) 
    self.tree.Branch("LT"              ,  self.LT              , "LT/F"               ) 
    self.tree.Branch("ST"              ,  self.ST              , "ST/F"               ) 
    self.tree.Branch("LeptonOnePt"     ,  self.LeptonOnePt     , "LeptonOnePt/F"      ) 
    self.tree.Branch("LeptonMETTMass"  ,  self.LeptonMETTMass  , "LeptonMETTMass/F"   ) 
    self.tree.Branch("LeptonMETDeltaPhi",  self.LeptonMETDeltaPhi, "LeptonMETDeltaPhi/F" ) 

                                            
  def endJob(self):                         
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    
    self.evt[0]             = event.event & 0xffffffffffffffff 
    # NO CUT
    self.cutflow.Fill(self.cut_none)
    ## needed for sumbinw######################################
    if self.isdata:
      self.cutflow.Fill(self.cut_weight, 1.)
    else:
      self.cutflow.Fill(self.cut_weight, event.genWeight)
    ###########################################################
    
    # TRIGGER
    if self.era=="2016" or self.era=="UL2016":
      if not (event.HLT_IsoMu24 and event.HLT_IsoTkMu24) : return False
    elif self.era=="2017" or self.era=="UL2017":
      if not (event.HLT_IsoMu24 and event.HLT_IsoMu27) : return False
    elif self.era=="2018" or self.era=="UL2018":
      if not event.HLT_IsoMu24 : return False
    self.cutflow.Fill(self.cut_trig)
    
    # SELECT MUONS
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if muon.pt<10: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.tightId: continue
      if muon.pfRelIso04_all>0.50: continue
      muons.append(muon)
    if len(muons)!=1: return False
    # apply trigger matching#######
    MatchedTrigger = False
    for selmuon in muons:
      # if not self.trigger.match(event,muon): continue ## fixme
      if selmuon.pt<self.muonTrgPt : continue
      MatchedTrigger = True
    if not MatchedTrigger : return False
    ################################
    self.cutflow.Fill(self.cut_muon)

    # SELECT JET AS A FAKE TAU CANDINDATE
    jets = [ ]
    for jet in Collection(event,'Jet'):
      if abs(jet.eta)>2.3: continue #4.7: continue
      if any(jet.DeltaR(muon)<0.4 for muon in muons): continue ## remove overlap with selected muons as well !?! dR<0.4 optimal???
      if jet.jetId<2: continue # Tight
      if jet.pt<=self.jetCutPt: continue
      jets.append(jet)
    if len(jets)!=1: return False ## require at most one central jet, to be used as fake tau candidate

    for jet in Collection(event,'Jet'):
      if abs(jet.eta)>=2.3 and abs(jet.eta)<4.7 and jet.pt>self.jetCutPt:
        return False ## There should be no forward jets

    self.cutflow.Fill(self.cut_fake)    

    # SELECT TAU 
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if tau.pt<20: continue
      if abs(tau.eta)>2.3: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,10,11]: continue
      if abs(tau.charge)!=1: continue
      # ask these two in the plotting part
      #if tau.idDeepTau2017v2p1VSe<16: continue # medium Vse
      #if tau.idDeepTau2017v2p1VSmu<8: continue # tight Vsmu 
      #####################################
      if tau.idDeepTau2017v2p1VSjet<1: continue # require minimum WP
      if jet.DeltaR(tau)>0.3: continue # make sure the tau matches to the fake tau candidate
      taus.append(tau)
    if len(taus)!=1:
      return False 
    self.cutflow.Fill(self.cut_tau)

    # Calculate MET
    MET     = event.MET_pt    
    MET_phi = event.MET_phi
    #if self.ismc:
    #  dp = taus[0].tlv*(1.-1./taus[0].es) # assume shift is already applied     
    #  correctmet(met,dp)

    # Leptons
    tau   = taus[0] # max(taus,key=lambda p: p.pt)
    muon0 = muons[0]
    # Fake Tau candidate
    jet   = jets[0]

    # Leptons dR
    #muon = max(muons,key=lambda p: p.pt)
    if muon0.DeltaR(jet)<0.4:   return False
    if muon0.DeltaR(tau)<0.4:   return False
    self.cutflow.Fill(self.cut_pair)
    
    # VETO for extraMuons
    looseMuons = [ ]    
    for muon in Collection(event,'Muon'):
      if muon.pt<10: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if muon.pfRelIso04_all>0.3: continue
      if muon.DeltaR(jet)<0.4: continue 
      if muon.DeltaR(tau)<0.4: continue 
      if muon.looseId and all(m._index!=muon._index for m in muons):
        looseMuons.append(muon)
    if len(looseMuons)>0 : return False
    self.cutflow.Fill(self.cut_loosemu)
    
    # VETO ELECTRONS
    Electrons = []
    for electron in Collection(event,'Electron'):
      if electron.pt<10: continue
      if abs(electron.eta)>2.5: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if electron.pfRelIso03_all>0.3: continue
      if electron.DeltaR(jet)<0.4: continue
      if electron.DeltaR(tau)<0.4: continue
      if any(electron.DeltaR(muon)<0.3 for muon in muons): continue ## remove overlap with selected muons as well !?! dR<0.3 optimal???
      if electron.convVeto==1 and electron.lostHits<=1 and electron.mvaFall17V2noIso_WPL:
        Electrons.append(electron)
    if len(Electrons)>0 : return False
    self.cutflow.Fill(self.cut_elecveto)
    
    # WEIGHTS AND CORRECTIONS
    # EVENT WEIGHTS
    self.lumi[0]            = event.luminosityBlock
    self.metfilter[0]       = self.metfilt(event)
    
    if self.ismc : 
      self.npu[0]           = event.Pileup_nPU
      self.npu_true[0]      = event.Pileup_nTrueInt
      try:
        self.NUP[0]         = event.LHE_Njets ##number of partons for stitching (LHE_Njets)
      except RuntimeError:
        self.NUP[0]         = -1        
      self.genweight[0]     = event.genWeight
      self.puweight[0]      = self.puTool.getWeight(event.Pileup_nTrueInt)
      # Z and Top pT weights
      if self.dozpt:
        zboson = getzboson(event)
        self.m_moth[0]      = zboson.M()
        self.pt_moth[0]     = zboson.Pt()
        self.zptweight[0]   = self.zptTool.getZptWeight(zboson.Pt(),zboson.M())
      elif self.dotoppt:
        toppt1, toppt2      = gettoppt(event)
        self.pt_moth1[0]    = max(toppt1,toppt2)
        self.ttptweight[0]  = getTopPtWeight(toppt1,toppt2)
      # MUON WEIGHTS
      self.trigweight[0]    = self.muSFs.getTriggerSF(muon0.pt,muon0.eta) # assume leading muon was triggered on
      self.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon0.pt,muon0.eta)
      # TAU WEIGHTS
      self.idweightTdm_tau[0]  = -1.0
      self.idweightT_tau[0]    = -1.0
      self.idweightM_tau[0]    = -1.0
      self.idweightVVVL_tau[0] = -1.0
      self.ltfweight_tau[0]    = 1.0
      self.ltfweight_tau[0]    = 1.0
      
      if tau.genPartFlav==5: # real tau
        self.idweightTdm_tau[0]  = self.tauSFsT_dm.getSFvsDM(tau.pt,tau.decayMode)
        self.idweightT_tau[0]    = self.tauSFsT.getSFvsPT(tau.pt)
        self.idweightM_tau[0]    = self.tauSFsM.getSFvsPT(tau.pt) 
        self.idweightVVVL_tau[0] = self.tauSFsVVVL.getSFvsPT(tau.pt)
      elif tau.genPartFlav in [1,3]: # e -> tau fake                       
        self.ltfweight_tau[0]    = self.etfSFs.getSFvsEta(tau.eta,tau.genPartFlav)
      elif tau.genPartFlav in [2,4]: # mu -> tau fake                             
        self.ltfweight_tau[0]    = self.mtfSFs.getSFvsEta(tau.eta,tau.genPartFlav)


    # SAVE CONTROL VARIABLES
    self.pt_mu0[0]   = muon0.pt
    self.eta_mu0[0]  = muon0.eta
    self.q_mu0[0]    = muon0.charge
    self.id_mu0[0]   = muon0.tightId
    self.iso_mu0[0]  = muon0.pfRelIso04_all
    self.pt_tau[0]   = tau.pt
    self.eta_tau[0]  = tau.eta
    self.q_tau[0]    = tau.charge
    self.id_tau[0]   = tau.idDeepTau2017v2p1VSjet
    self.iso_tau[0]  = tau.rawIso

    isGenuineTau = False
    isGenuineTau = getIsGenuineTau(self,tau)
    #print "Tau has pt=%s, eta=%s, dz = %s, genPartFlav = %s"%(tau.pt, tau.eta, tau.dz, tau.genPartFlav)
    
    # Event Vars
    HT = 0.0
    LT = 0.0
    ST = 0.0
  
    for jet in jets: HT += jet.pt
    for mu in muons: LT += mu.pt
    LT += tau.pt
    ST = HT + LT + MET
    
    #LeptonMET Vars
    muon0.tlv = muon0.p4()
    MET_Px    = MET*cos(MET_phi)
    MET_Py    = MET*sin(MET_phi)
    #Calculate TMass(muon,MET)
    ETsum = MET + muon0.tlv.Et()
    xsum  = MET*cos(MET_phi) + muon0.tlv.Px()
    ysum  = MET*sin(MET_phi) + muon0.tlv.Py()
    TMassSquared = (ETsum*ETsum) - (xsum*xsum) - (ysum*ysum)
    if(TMassSquared >= 0) :
      TMass_leptonMET = sqrt(TMassSquared) 
    else :
      TMass_leptonMET = 0

    # if TMass_leptonMET < 60.0 : return False
    
    ##jet to tau fake rate method
    JetPt             = jet.pt  
    JetEta            = jet.eta 
    TauIsGenuine      = isGenuineTau
    TauPt             = tau.pt
    TauEta            = tau.eta
    TauDM             = tau.decayMode
    TauIdVSe          = tau.idDeepTau2017v2p1VSe
    TauIdVSmu         = tau.idDeepTau2017v2p1VSmu
    JetN              = len(jets)
    LeptonOnePt       = muon0.pt
    LeptonMETTMass    = TMass_leptonMET
    LeptonMETDeltaPhi = deltaPhi(muon0.phi,MET_phi)
    
    self.JetPt[0]              = JetPt           
    self.JetEta[0]             = JetEta     
    self.TauIsGenuine[0]       = TauIsGenuine
    self.TauPt[0]              = TauPt           
    self.TauEta[0]             = TauEta          
    self.TauDM[0]              = TauDM
    self.TauIdVSe[0]           = TauIdVSe
    self.TauIdVSmu[0]          = TauIdVSmu
    self.JetN[0]               = JetN       
    self.MET[0]                = MET              
    self.HT[0]                 = HT            
    self.LT[0]                 = LT            
    self.ST[0]                 = ST            
    self.LeptonOnePt[0]        = LeptonOnePt     
    self.LeptonMETTMass[0]     = LeptonMETTMass
    self.LeptonMETDeltaPhi[0]  = LeptonMETDeltaPhi
    
    #Fill Histos
    self.tree.Fill()
    
    return True

## Functions
def getIsGenuineTau(self,tau):
  if not self.ismc : return False

  if tau.genPartFlav==5: # genuine tau
    return True
  else:
    return False
