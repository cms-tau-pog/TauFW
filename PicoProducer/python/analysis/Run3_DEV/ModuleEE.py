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
from TauFW.PicoProducer.corrections.ElectronSFs import *

class ModuleEE(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'mumu'
    super(ModuleEE,self).__init__(fname,**kwargs)
    self.out     = TreeProducerMuMu(fname,self)
    self.zwindow = kwargs.get('zwindow', False ) # stay between 70 and 110 GeV
    
       
    # CORRECTIONS
    if self.ismc:
      self.eleSFs   = ElectronSFs(era=self.era) # ele id/iso/trigger SFs 

    # TRIGGERS
    y_trig = self.year
    if "2022" in self.era:
       y_trig = 2018
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(y_trig))
    self.trigger   = TrigObjMatcher(jsonfile,trigger='SingleElectron',isdata=self.isdata)
    self.ele1CutPt  = self.trigger.ptmins[0]
    self.ele2CutPt = 15
    self.tauCutPt  = 20
    self.eleCutEta = 2.1
    self.tauCutEta = 2.3
 
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('electron',     "electron"                       )
    self.out.cutflow.addcut('pair',         "pair"                       )
    self.out.cutflow.addcut('leadTrig',     "leading ele triggered"     ) # ADDED FOR SF CROSS CHECKS!
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
    super(ModuleEE,self).beginJob()
    print(">>> %-12s = %s"%('ele1CutPt', self.ele1CutPt))
    print(">>> %-12s = %s"%('ele2CutPt', self.ele2CutPt))
    print(">>> %-12s = %s"%('eleCutEta', self.eleCutEta))
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
      if electron.pt<self.ele2CutPt: continue
      if abs(electron.eta)>self.eleCutEta: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if not electron.convVeto: continue
      if electron.lostHits>1: continue
      if electron.pfRelIso03_all > 0.5: continue
      if not electron.mvaFall17V2noIso_WP90: continue
      if not self.trigger.match(event,electron): continue
      electrons.append(electron)
    if len(electrons)==0:
      return False
    self.out.cutflow.fill('electron')   
        
    ##### EE PAIR #################################
    dileps = [ ]
    ptcut  = self.ele1CutPt # trigger dependent
    for i, ele1 in enumerate(electrons,1):
      for ele2 in electrons[i:]:
        if ele2.DeltaR(ele1)<0.5: continue
        if ele1.pt<ptcut and ele2.pt<ptcut: continue # larger pt cut
        if self.zwindow and not (70<(ele1.p4()+ele2.p4()).M()<110): continue # Z mass
        ltau = LeptonPair(ele1,ele1.pfRelIso03_all,ele2,ele2.pfRelIso03_all)
        dileps.append(ltau)
    if len(dileps)==0:
      return False
    ele1, ele2 = max(dileps).pair
    ele1.tlv    = ele1.p4()
    ele2.tlv    = ele2.p4()
    self.out.cutflow.fill('pair')
    
    # ADDED FOR SF CROSS CHECKS!
    # Only keep events with leading ele triggered
    if not self.trigger.match(event,ele1): 
      return False
    self.out.cutflow.fill('leadTrig')
    
    # VETOS
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[ele1,ele2],[ ],[ ],self.channel, era=self.era)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = extramuon_veto, extraelec_veto, dilepton_veto
    self.out.lepton_vetoes[0]       = extramuon_veto or extraelec_veto or dilepton_veto
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # ELE 1
    self.out.pt_1[0]       = ele1.pt
    self.out.eta_1[0]      = ele1.eta
    self.out.phi_1[0]      = ele1.phi
    self.out.m_1[0]        = ele1.mass
    self.out.y_1[0]        = ele1.tlv.Rapidity()
    self.out.dxy_1[0]      = ele1.dxy
    self.out.dz_1[0]       = ele1.dz
    self.out.q_1[0]        = ele1.charge
    self.out.iso_1[0]      = ele1.pfRelIso03_all # relative isolation
    #self.out.tkRelIso_1[0] = ele1.tkRelIso
    self.out.idMedium_1[0] = ele1.mvaFall17V2noIso_WP90
    #self.out.idTight_1[0]  = ele1.tightId
    #self.out.idHighPt_1[0] = ele1.highPtId
    
    
    # ELE 2
    self.out.pt_2[0]       = ele2.pt
    self.out.eta_2[0]      = ele2.eta
    self.out.phi_2[0]      = ele2.phi
    self.out.m_2[0]        = ele2.mass
    self.out.y_2[0]        = ele2.tlv.Rapidity()
    self.out.dxy_2[0]      = ele2.dxy
    self.out.dz_2[0]       = ele2.dz
    self.out.q_2[0]        = ele2.charge
    self.out.iso_2[0]      = ele2.pfRelIso03_all # relative isolation
    #self.out.tkRelIso_2[0] = ele2.tkRelIso
    self.out.idMedium_2[0] = ele2.mvaFall17V2noIso_WP90
    #self.out.idTight_2[0]  = ele2.tightId
    #self.out.idHighPt_2[0] = ele2.highPtId
    
    
    # TAU for jet -> tau fake rate measurement in mumu+tau events
    maxtau = None
    ptmax  = 20
    for tau in Collection(event,'Tau'):
      if tau.pt<ptmax: continue
      if ele1.DeltaR(tau)<0.5: continue
      if ele2.DeltaR(tau)<0.5: continue
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
      self.out.genmatch_1[0] = ele1.genPartFlav
      self.out.genmatch_2[0] = ele2.genPartFlav
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,ele1,ele2)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if ele1.pfRelIso03_all<0.50 and ele2.pfRelIso03_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # ELE WEIGHTS
      self.out.trigweight[0]    = self.eleSFs.getTriggerSF(ele1.pt,abs(ele1.eta)) # assume leading ele was triggered on
      self.out.idisoweight_1[0] = self.eleSFs.getIdIsoSF(ele1.pt,abs(ele1.eta))
      self.out.idisoweight_2[0] = self.eleSFs.getIdIsoSF(ele2.pt,abs(ele2.eta))
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,ele1,ele2,met,met_vars)
    
    
    self.out.fill()
    return True
    
