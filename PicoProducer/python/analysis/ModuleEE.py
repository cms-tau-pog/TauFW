# Author: Izaak Neutelings (June 2024)
# Description: Analysis module to pre-select ee events
import sys
import numpy as np
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.analysis.TreeProducerEE import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonPair
from TauFW.PicoProducer.corrections.ElectronSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import TrigObjMatcher


class ModuleEE(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'ee'
    super(ModuleEE,self).__init__(fname,**kwargs)
    self.out     = TreeProducerEE(fname,self)
    self.zwindow = kwargs.get('zwindow', False ) # stay between 70 and 110 GeV
    
    # TRIGGERS
    jsonfile        = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger    = TrigObjMatcher(jsonfile,trigger='SingleElectron',isdata=self.isdata)
    self.ele1CutPt  = self.trigger.ptmins[0]
    self.ele2CutPt  = 15
    self.ele1CutEta = 2.3
    self.ele2CutEta = 2.3
    
    # CORRECTIONS
    if self.ismc:
      self.eleSFs  = ElectronSFs(era=self.era) # electron id/iso/trigger SFs
    
    # CUTFLOW
    self.out.cutflow.addcut('weight',   "no cut, weighted" ) # use for normalization with sum of weight
    self.out.cutflow.addcut('none',     "no cut"           ) # number of processed events
    self.out.cutflow.addcut('trig',     "trigger"          )
    self.out.cutflow.addcut('electron', "electron"         )
    self.out.cutflow.addcut('pair',     "pair"             )
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleEE,self).beginJob()
    print(">>> %-12s = %s"%('ele1CutPt',  self.ele1CutPt))
    print(">>> %-12s = %s"%('ele1CutEta', self.ele1CutEta))
    print(">>> %-12s = %s"%('ele2CutPt',  self.ele2CutPt))
    print(">>> %-12s = %s"%('ele2CutEta', self.ele2CutEta))
    print(">>> %-12s = %s"%('zwindow',    self.zwindow))
    
  
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
    
    
    ##### ELECTRON ###################################
    electrons = [ ]
    for electron in Collection(event,'Electron'):
      #if self.ismc and self.ees!=1:
      #  electron.pt   *= self.ees
      #  electron.mass *= self.ees
      if electron.pt<self.ele2CutPt: continue
      if abs(electron.eta)>self.ele2CutEta: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if not electron.convVeto: continue
      if electron.lostHits>1: continue
      if not (electron.mvaFall17V2Iso_WP90 or electron.mvaFall17V2noIso_WP90): continue
      if not self.trigger.match(event,electron): continue
      electrons.append(electron)
    if len(electrons)==0:
      return False
    self.out.cutflow.fill('electron')
    
    
    ##### EE PAIR ####################################
    dileps = [ ]
    for i, electron1 in enumerate(electrons,1):
      for electron2 in electrons[i:]:
        if electron2.DeltaR(electron1)<0.5: continue
        if electron1.pt<self.ele1CutPt and electron2.pt<self.ele1CutPt: continue # larger pt cut
        if self.zwindow and not (70<(electron1.p4()+electron2.p4()).M()<110): continue # Z mass
        dilep = LeptonPair(electron1,electron1.pfRelIso03_all,electron2,electron2.pfRelIso03_all)
        dileps.append(dilep)
    if len(dileps)==0:
      return False
    electron1, electron2 = max(dileps).pair
    electron1.tlv = electron1.p4()
    electron2.tlv = electron2.p4()
    self.out.cutflow.fill('pair')
    
    
    # VETOS
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[electron1,electron2],[ ],[ ],self.channel,self.era)
    self.out.lepton_vetoes[0] = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    
    
    # EVENT
    self.fillEventBranches(event)
    
    
    # LEADING ELECTRON
    self.out.pt_1[0]            = electron1.pt
    self.out.eta_1[0]           = electron1.eta
    self.out.phi_1[0]           = electron1.phi
    self.out.m_1[0]             = electron1.mass
    self.out.y_1[0]             = electron1.tlv.Rapidity()
    self.out.dxy_1[0]           = electron1.dxy
    self.out.dz_1[0]            = electron1.dz
    self.out.q_1[0]             = electron1.charge
    self.out.iso_1[0]           = electron1.pfRelIso03_all
    self.out.cutBased_1[0]      = electron1.cutBased
    self.out.mvaIso_WP90_1[0]   = electron1.mvaFall17V2Iso_WP90
    self.out.mvaIso_WP80_1[0]   = electron1.mvaFall17V2Iso_WP80
    self.out.mvanoIso_WP90_1[0] = electron1.mvaFall17V2noIso_WP90
    self.out.mvanoIso_WP80_1[0] = electron1.mvaFall17V2noIso_WP80
    
    
    # SUBLEADING TAU
    self.out.pt_2[0]            = electron2.pt
    self.out.eta_2[0]           = electron2.eta
    self.out.phi_2[0]           = electron2.phi
    self.out.m_2[0]             = electron2.mass
    self.out.y_2[0]             = electron2.tlv.Rapidity()
    self.out.dxy_2[0]           = electron2.dxy
    self.out.dz_2[0]            = electron2.dz
    self.out.q_2[0]             = electron2.charge
    self.out.iso_2[0]           = electron2.pfRelIso03_all
    self.out.cutBased_2[0]      = electron2.cutBased
    self.out.mvaIso_WP90_2[0]   = electron2.mvaFall17V2Iso_WP90
    self.out.mvaIso_WP80_2[0]   = electron2.mvaFall17V2Iso_WP80
    self.out.mvanoIso_WP90_2[0] = electron2.mvaFall17V2noIso_WP90
    self.out.mvanoIso_WP80_2[0] = electron2.mvaFall17V2noIso_WP80
    
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = electron1.genPartFlav
      self.out.genmatch_2[0] = electron2.genPartFlav
    
    
    # JETS
    jets, met, njets_vars, met_vars = self.fillJetBranches(event,electron1,electron2)
    
    
    # WEIGHTS
    if self.ismc:
      self.fillCommonCorrBranches(event,jets,met,njets_vars,met_vars)
      if electron1.pfRelIso03_all<0.50 and electron2.pfRelIso03_all<0.50:
        self.btagTool.fillEffMaps(jets,usejec=self.dojec)
      
      # ELECTRON WEIGHTS
      self.out.trigweight[0]    = self.eleSFs.getTriggerSF(electron1.pt,electron1.eta)
      self.out.idisoweight_1[0] = self.eleSFs.getIdIsoSF(electron1.pt,electron1.eta)
      self.out.idisoweight_2[0] = self.eleSFs.getIdIsoSF(electron2.pt,electron2.eta)
      self.out.weight[0]        = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0]*self.out.idisoweight_2[0]
      
    elif self.isembed:
      ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
      self.out.genweight[0]     = event.genWeight
    
    
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,electron1,electron2,met,met_vars)
    
    
    self.out.fill()
    return True
    
