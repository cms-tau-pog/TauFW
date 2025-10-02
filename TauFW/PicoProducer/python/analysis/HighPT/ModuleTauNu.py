# Author: Alexei Raspereza (December 2022)
# Description: Module to preselect W*->tau+v events
import sys
import numpy as np
import math
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.analysis.TreeProducerTauNu import *
from TauFW.PicoProducer.analysis.ModuleHighPT import *
from TauFW.PicoProducer.analysis.utils import loosestIso, idIso, matchgenvistau, matchtaujet
from TauFW.PicoProducer.corrections.TrigObjMatcher import TrigObjMatcher
from TauFW.PicoProducer.corrections.TauTriggerSFs import TauTriggerSFs
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool, TauFESTool
from TauFW.PicoProducer.corrections.MetTriggerSF import METTriggerSF
from TauFW.PicoProducer.corrections.WmassCorrection import WStarWeight 
from ROOT import TLorentzVector

class ModuleTauNu(ModuleHighPT):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'taunu'
    super(ModuleTauNu,self).__init__(fname,**kwargs)

    # conservative unc
    self.tes_shift = 0.03
    self.unc_names  = ['taues','taues_1pr','taues_1pr1pi0','taues_3pr','taues_3pr1pi0']
    self.tes_uncs = [ u+v for u in self.unc_names for v in ['Up','Down'] ]  

    self.out = TreeProducerTauNu(fname,self)

    # loose pre-selection cuts
    self.tauPtCut  = 90
    self.tauEtaCut = 2.3
    self.metCut    = 90
    self.mtCut     = 150
    self.dphiCut   = 2.2

    # CORRECTIONS
    if self.ismc:
      # MET trigger corrections
      filename = 'mettrigger_'+self.era+'.root'
      self.trig_corr       = METTriggerSF(filename)

      # WStar mass reweighting
      filename = 'kfactor_tau.root'
      if self.year==2016: filename = 'kfactor_tau_2016.root'
      self.wmass_corr = WStarWeight(filename,'kfactor_tau')
    
    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                      )
    self.out.cutflow.addcut('trigger',      "trigger"                     )
    self.out.cutflow.addcut('tau',          "tau"                         )
    self.out.cutflow.addcut('met',          "met"                         )
    self.out.cutflow.addcut('mT',           "mT"                          )
    self.out.cutflow.addcut('dphi',         "DPhi"                        )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15        )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16  ) # use for normalization
    
  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleTauNu,self).beginJob()
    print(">>> %-12s = %s"%('tauPtCut',   self.tauPtCut))
    print(">>> %-12s = %s"%('tauEtaCut',  self.tauEtaCut))
    print(">>> %-12s = %s"%('metCut',     self.metCut))
    print(">>> %-12s = %s"%('mtCut',      self.mtCut))
    print(">>> %-12s = %s"%('dphiCut',    self.dphiCut))
    print(">>> %-12s = %s"%('tes_shift',  self.tes_shift))

  # should be run after filling met and tau branches
  def FillTESshifts(self):  

    # initializing taues uncertainty variables
    for unc in self.tes_uncs:      
      getattr(self.out,'met_'+unc)[0]  = self.out.met[0]
      getattr(self.out,'metphi_'+unc)[0] = self.out.metphi[0]
      getattr(self.out,'pt_1_'+unc)[0] = self.out.pt_1[0]
      getattr(self.out,'m_1_'+unc)[0]  = self.out.m_1[0]
      getattr(self.out,'mt_1_'+unc)[0] = self.out.mt_1[0]
      getattr(self.out,'metdphi_1_'+unc)[0] = self.out.metdphi_1[0]

    unc_name=''  
    if self.out.dm_1[0]==0: unc_name='taues_1pr'
    elif self.out.dm_1[0]==1 or self.out.dm_1[0]==2: unc_name='taues_1pr1pi0'
    elif self.out.dm_1[0]==10: unc_name='taues_3pr'
    elif self.out.dm_1[0]==11: unc_name='taues_3pr1pi0'

    shifts = {'Up':True, 'Down':False}
    for shift in shifts:
      met_shift, pt_shift, metdphi_shift, mt_shift, mass_shift = self.PropagateTESshift(shifts[shift])
      unc_incl = 'taues'+shift
      unc_dm = unc_name+shift
      for unc in [unc_incl, unc_dm]:
        getattr(self.out,'met_'+unc)[0]  = met_shift.Pt()
        getattr(self.out,'metphi_'+unc)[0] = met_shift.Phi()
        getattr(self.out,'pt_1_'+unc)[0] = pt_shift.Pt()
        if self.out.dm_1[0]>0: getattr(self.out,'m_1_'+unc)[0]  = mass_shift
        getattr(self.out,'mt_1_'+unc)[0] = mt_shift
        getattr(self.out,'metdphi_1_'+unc)[0] = metdphi_shift
        

  # should be run after filling met and tau branches!
  def PropagateTESshift(self,up):
    
    metx = self.out.met[0]*math.cos(self.out.metphi[0])
    mety = self.out.met[0]*math.sin(self.out.metphi[0])
    met = TLorentzVector()
    met.SetXYZT(metx,mety,0,self.out.met[0])

    ptx = self.out.pt_1[0]*math.cos(self.out.phi_1[0])
    pty = self.out.pt_1[0]*math.sin(self.out.phi_1[0])
    pt = TLorentzVector()
    pt.SetXYZT(ptx,pty,0,self.out.pt_1[0])

    scale = 1.0 - self.tes_shift
    if up:
      scale = 1.0 + self.tes_shift

    
    ptx_shift = scale * pt.Px()
    pty_shift = scale * pt.Py()
    ptTot_shift = scale * pt.Pt()
    pt_shift = TLorentzVector()
    pt_shift.SetXYZT(ptx_shift,pty_shift,0,ptTot_shift)
    met_shift = met + pt - pt_shift
    mass_shift = scale * self.out.m_1[0]
    metdphi_shift = abs(met_shift.DeltaPhi(pt_shift))
    mt_shift = math.sqrt(2.0 * pt_shift.Pt() * met_shift.Pt() * (1.0 - math.cos(metdphi_shift) ) )

    return met_shift, pt_shift, metdphi_shift, mt_shift, mass_shift
    
  
  def analyze(self, event):
    """Process and pre-select events; fill branches and return True if the events passes,
    return False otherwise."""
    sys.stdout.flush()
    
    
    ##### NO CUT #####################################
    if not self.fillhists(event):
      return False
    
    if not event.HLT_PFMETNoMu120_PFMHTNoMu120_IDTight:
      return False
    self.out.cutflow.fill('trigger')

    
    ##### TAU ########################################
    taus = [ ]
    for tau in Collection(event,'Tau'):
      if abs(tau.eta)>self.tauEtaCut: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,2,10,11]: continue
      if abs(tau.charge)!=1: continue
      if tau.idDeepTau2017v2p1VSe<1: continue   # VVVLoose
      if tau.idDeepTau2017v2p1VSmu<1: continue  # VLoose
      if tau.idDeepTau2017v2p1VSjet<1: continue  # VVVLoose
      if tau.pt<self.tauPtCut: continue
      taus.append(tau)
    if len(taus)==0:
      return False
    self.out.cutflow.fill('tau')
    tau1 = max(taus,key=lambda p: p.pt)

    # JETS
    leptons = [tau1]
    jets, ht_muons, met, met_vars = self.fillJetMETBranches(event,leptons,tau1)

    if met.Pt()<self.metCut:
      return False
    self.out.cutflow.fill('met')

    if self.out.mt_1[0]<self.mtCut:
      return False
    self.out.cutflow.fill('mT')

    if self.out.metdphi_1[0]<self.dphiCut:
      return False
    self.out.cutflow.fill('dphi')

    # VETOS
    self.out.extramuon_veto[0] = self.get_extramuon_veto(event,[tau1]) 
    self.out.extraelec_veto[0] = self.get_extraelec_veto(event,[tau1]) 
    self.out.extratau_veto[0]  = self.get_extratau_veto(event,[tau1])
    
    # EVENT
    self.fillEventBranches(event)
        
    # TAU 1
    self.out.pt_1[0]                       = tau1.pt
    self.out.eta_1[0]                      = tau1.eta
    self.out.phi_1[0]                      = tau1.phi
    self.out.m_1[0]                        = tau1.mass
    self.out.dxy_1[0]                      = tau1.dxy
    self.out.dz_1[0]                       = tau1.dz
    self.out.q_1[0]                        = tau1.charge
    self.out.dm_1[0]                       = tau1.decayMode
    self.out.rawDeepTau2017v2p1VSe_1[0]    = tau1.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_1[0]   = tau1.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_1[0]  = tau1.rawDeepTau2017v2p1VSjet
    self.out.idDeepTau2017v2p1VSe_1[0]     = tau1.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_1[0]    = tau1.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_1[0]   = tau1.idDeepTau2017v2p1VSjet
    jpt_match, jpt_genmatch = matchtaujet(event,tau1,self.ismc)
    if jpt_match>10:
      self.out.jpt_match_1[0] = jpt_match
    else:
      self.out.jpt_match_1[0] = self.out.pt_1[0]
    self.out.jpt_ratio_1[0] = self.out.pt_1[0]/self.out.jpt_match_1[0]
    

    # GENERATOR 
    if self.ismc:
      self.out.genmatch_1[0]     = tau1.genPartFlav
     
      pt1, eta1, phi1, status1   = matchgenvistau(event,tau1)
      
      self.out.genvistaupt_1[0]  = pt1
      self.out.genvistaueta_1[0] = eta1
      self.out.genvistauphi_1[0] = phi1
      self.out.gendm_1[0]        = status1
      if jpt_genmatch>10:
        self.out.jpt_genmatch_1[0] = jpt_genmatch
      else:
        self.out.jpt_genmatch_1[0] = pt1

      self.FillTESshifts()
        
      
    # WEIGHTS
    self.out.weight[0] = 1.0 # for data
    if self.ismc:
      self.fillCommonCorrBranches(event)
      self.out.trigweight[0] = self.trig_corr.getWeight(self.out.metnomu[0],self.out.mhtnomu[0])
      self.out.idisoweight_1[0] = 1.0    

      # KFACTOR_TAU
      if self.dowmasswgt:
        wMass = 81
        for genpart in Collection(event,'GenPart'):
          if genpart.statusFlags < 8192: continue
          if abs(genpart.pdgId) == 24:
            wMass=genpart.mass    
        self.out.kfactor_tau[0] = self.wmass_corr.getWeight(wMass)

      # total weight ->
      self.out.weight[0] = self.out.trigweight[0]*self.out.puweight[0]*self.out.genweight[0]*self.out.idisoweight_1[0]

      if self.dowmasswgt:
        self.out.weight[0] *= self.out.kfactor_tau[0]
      if self.dozpt:
        self.out.weight[0] *= self.out.zptweight[0]
      if self.dotoppt:
        self.out.weight[0] *= self.out.ttptweight[0]

    self.out.fill()
    return True
    
