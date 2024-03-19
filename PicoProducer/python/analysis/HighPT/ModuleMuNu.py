# Authors: Jacopo Malvaso and Alexei Raspereza (December 2022)
# Description: selector of W*->muv events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerMuNu import *
from TauFW.PicoProducer.analysis.ModuleHighPT import *
from TauFW.PicoProducer.analysis.utils import idIso, matchtaujet 
from TauFW.PicoProducer.corrections.MuonSFs import *
from TauFW.PicoProducer.corrections.WmassCorrection import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
from TauFW.PicoProducer import datadir

class ModuleMuNu(ModuleHighPT):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'munu'
    super(ModuleMuNu,self).__init__(fname,**kwargs)
    self.out     = TreeProducerMuNu(fname,self)

    # Cuts (W->mu+vu)
    self.muonPtCut = 80
    self.muonEtaCut = 2.4
    self.metCut = 50
    self.mtCut  = 40
    
    # TRIGGERS
    print('+++++++++++++++++')
    print('YEAR   ',self.year)
    print('+++++++++++++++++')
    
    jsonfile = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(self.year))
    self.trigger = TrigObjMatcher(jsonfile,trigger='SingleMuon',isdata=self.isdata)    

    print("ModuleMuNu, era=",self.era)
    # CORRECTIONS
    if self.ismc:
      self.muSFs   = MuonSFs(era=self.era)
    
    filename = 'kfactor_mu.root'
    if self.year==2016:
      filename = 'kfactor_mu_2016.root'
    self.wmass_corr = WStarWeight(filename,'kfactor_mu')

    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('muon',         "muon"                       )
    self.out.cutflow.addcut('met' ,         "met"                        )
    self.out.cutflow.addcut('mT' ,          "mT cut"                     )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization

  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleMuNu,self).beginJob()
   
    pass
    
  
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

    ##### MUON #######################################
    muons = [ ]
    for muon in Collection(event,'Muon'):
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.mediumId: continue
      if muon.pfRelIso04_all>0.3: continue
      if muon.pt<self.muonPtCut: continue
      if abs(muon.eta)>self.muonEtaCut: continue
      if not self.trigger.match(event,muon): continue
      muons.append(muon)
    if len(muons)==0:
      return False
    self.out.cutflow.fill('muon')
    muon1 = max(muons,key=lambda p: p.pt)

    # JETS
    leptons = [muon1]
    jets, ht_muons, met, met_vars = self.fillJetMETBranches(event,leptons,muon1) 
    
    if met.Pt() < self.metCut:
      return False
    self.out.cutflow.fill('met')

    # MET VARIABLES
    if self.out.mt_1[0]<self.mtCut:
      return False
    self.out.cutflow.fill('mT')
        
    # VETOS
    self.out.extramuon_veto[0] = self.get_extramuon_veto(event,leptons)
    self.out.extraelec_veto[0] = self.get_extraelec_veto(event,leptons)
    self.out.extratau_veto[0] = self.get_extratau_veto(event,leptons)
    
    # EVENT
    self.fillEventBranches(event)
    
    # MUON 1
    self.out.pt_1[0]       = muon1.pt
    self.out.eta_1[0]      = muon1.eta
    self.out.phi_1[0]      = muon1.phi
    self.out.dxy_1[0]      = muon1.dxy
    self.out.dz_1[0]       = muon1.dz
    self.out.q_1[0]        = muon1.charge
    self.out.iso_1[0]      = muon1.pfRelIso04_all # relative isolation
    self.out.idMedium_1[0] = muon1.mediumId
    self.out.idTight_1[0]  = muon1.tightId
    self.out.idHighPt_1[0] = muon1.highPtId
    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0] = muon1.genPartFlav
    
    # WEIGHTS
    self.out.weight[0] = 1.0 # for data
    if self.ismc:
      self.fillCommonCorrBraches(event)
      # MUON WEIGHTS
      self.out.trigweight[0]    = self.muSFs.getTriggerSF(muon1.pt,muon1.eta) # muon trigger
      self.out.idisoweight_1[0] = self.muSFs.getIdIsoSF(muon1.pt,muon1.eta) # muon id and isolation SF

      # KFACTOR_MUON
      if self.dowmasswgt:
        wMass = 81
        for genpart in Collection(event,'GenPart'):
          if genpart.statusFlags < 8192: continue
          if abs(genpart.pdgId) == 24:
            wMass=genpart.mass    
        self.out.kfactor_mu[0] = self.wmass_corr.getWeight(wMass)

      # total weight ->
      self.out.weight[0] = self.out.trigweight[0]*self.out.puweight[0]*self.out.genweight[0]*self.out.idisoweight_1[0]
      if self.dowmasswgt:
        self.out.weight[0] *= self.out.kfactor_mu[0]
      if self.dozpt:
        self.out.weight[0] *= self.out.zptweight[0]
      if self.dotoppt:
        self.out.weight[0] *= self.out.ttptweight[0]

    self.out.fill()
    return True
  
  
