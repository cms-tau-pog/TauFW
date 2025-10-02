# Author: Paola Mastrapasqua (Nov 2023)
# Description: Simple module to pre-select etau events
import sys
import numpy as np
from TauFW.PicoProducer.analysis.TreeProducerETau import *
from TauFW.PicoProducer.analysis.ModuleTauPair import *
from TauFW.PicoProducer.analysis.utils import LeptonTauPair, loosestIso, idIso, matchgenvistau, matchtaujet, filtermutau
from TauFW.PicoProducer.corrections.ElectronSFs import *
from TauFW.PicoProducer.corrections.TrigObjMatcher import loadTriggerDataFromJSON, TrigObjMatcher
from TauPOG.TauIDSFs.TauIDSFTool import TauIDSFTool, TauESTool


class ModuleETau(ModuleTauPair):
  
  def __init__(self, fname, **kwargs):
    kwargs['channel'] = 'etau'
    super(ModuleETau,self).__init__(fname,**kwargs)
    self.out = TreeProducerETau(fname,self)
    print("=====> ERA: ", self.era)
    print("=====> YEAR: ", self.year) 
    
    # TRIGGERS
    y_trig = self.year
    if "2022" in self.era or "2023" in self.era:
       y_trig = 2018
    jsonfile       = os.path.join(datadir,"trigger/tau_triggers_%d.json"%(y_trig))
    self.trigger   = TrigObjMatcher(jsonfile,trigger='SingleElectron',isdata=self.isdata)
    self.eleCutPt  = self.trigger.ptmins[0]
    self.tauCutPt  = 20
    self.eleCutEta = 2.1
    self.tauCutEta = 2.5 
    
    #CORRECTIONS
    if self.ismc:
      self.eleSFs   = ElectronSFs(era=self.era) # ele id/iso/trigger SFs
    
    
    print("FES: ", self.fes)
    print("LTF: ", self.ltf)
    print("EES: ", self.ees) 
    print("RES: ", self.Zres)

    # CUTFLOW
    self.out.cutflow.addcut('none',         "no cut"                     )
    self.out.cutflow.addcut('trig',         "trigger"                    )
    self.out.cutflow.addcut('electron',     "electron"                   )
    self.out.cutflow.addcut('tau',          "tau"                        )
    self.out.cutflow.addcut('pair',         "pair"                       )
    #self.out.cutflow.addcut('muonveto',     "muon veto"                  )
    #self.out.cutflow.addcut('elecveto',     "electron veto"              )
    self.out.cutflow.addcut('lepvetoes',     "lep vetoes"              )
    self.out.cutflow.addcut('weight',       "no cut, weighted", 15       )
    self.out.cutflow.addcut('weight_no0PU', "no cut, weighted, PU>0", 16 ) # use for normalization
    ### Important cutflow entries to make stitching with exclusive mutauh sample
    self.out.cutflow.addcut('weight_mutaufilter', "no cut, mutaufilter", 17 )    
    self.out.cutflow.addcut('weight_mutaufilter_NUP0orp4', "no cut, weighted, mutau, 0 or >4 jets", 18 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP1', "no cut, weighted, mutau, 1 jet", 19 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP2', "no cut, weighted, mutau, 2 jets", 20 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP3', "no cut, weighted, mutau, 3 jets", 21 )
    self.out.cutflow.addcut('weight_mutaufilter_NUP4', "no cut, weighted, mutau, 4 jets", 22 )

  
  def beginJob(self):
    """Before processing any events or files."""
    super(ModuleETau,self).beginJob()
    print(">>> %-12s = %s"%('tauwp',      self.tauwp))
    print(">>> %-12s = %s"%('eleCutPt',   self.eleCutPt))
    print(">>> %-12s = %s"%('eleCutEta',  self.eleCutEta))
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
    if not self.trigger.fired(event): 
      return False
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
      if not electron.mvaFall17V2noIso_WP90: continue
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
          #print("ltf")
          tau.pt   *= self.ltf
          tau.mass *= self.ltf
          tau.es    = self.ltf
        elif self.fes and genmatch in [1,3]:
          #print("fes")
          tau.pt   *= self.fes
          tau.mass *= self.fes
          tau.es    = self.fes
        elif self.jtf!=1.0 and genmatch==0: # jet -> tau fake
          #print("jtf")
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
    extramuon_veto, extraelec_veto, dilepton_veto = getlepvetoes(event,[electron],[ ],[tau],self.channel,era=self.era)
    self.out.extramuon_veto[0], self.out.extraelec_veto[0], self.out.dilepton_veto[0] = getlepvetoes(event,[electron],[ ],[ ],self.channel,era=self.era)
    self.out.lepton_vetoes[0]       = self.out.extramuon_veto[0] or self.out.extraelec_veto[0] or self.out.dilepton_veto[0]
    self.out.lepton_vetoes_notau[0] = extramuon_veto or extraelec_veto or dilepton_veto
    

    #cutflow on veto
    if self.out.lepton_vetoes[0] and self.out.lepton_vetoes_notau[0]: return False
    self.out.cutflow.fill('lepvetoes')
   
 
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
    self.out.iso_2[0]                      = tau.rawIso
    self.out.rawDeepTau2017v2p1VSe_2[0]    = tau.rawDeepTau2017v2p1VSe
    self.out.rawDeepTau2017v2p1VSmu_2[0]   = tau.rawDeepTau2017v2p1VSmu
    self.out.rawDeepTau2017v2p1VSjet_2[0]  = tau.rawDeepTau2017v2p1VSjet
    
    self.out.rawDeepTau2018v2p5VSe_2[0]    = tau.rawDeepTau2018v2p5VSe
    self.out.rawDeepTau2018v2p5VSmu_2[0]   = tau.rawDeepTau2018v2p5VSmu
    self.out.rawDeepTau2018v2p5VSjet_2[0]  = tau.rawDeepTau2018v2p5VSjet

    self.out.idDecayMode_2[0]              = tau.idDecayMode
    self.out.idDecayModeNewDMs_2[0]        = tau.idDecayModeNewDMs
    self.out.idDeepTau2017v2p1VSe_2[0]     = tau.idDeepTau2017v2p1VSe
    self.out.idDeepTau2017v2p1VSmu_2[0]    = tau.idDeepTau2017v2p1VSmu
    self.out.idDeepTau2017v2p1VSjet_2[0]   = tau.idDeepTau2017v2p1VSjet

    self.out.idDeepTau2018v2p5VSe_2[0]     = tau.idDeepTau2018v2p5VSe
    self.out.idDeepTau2018v2p5VSmu_2[0]    = tau.idDeepTau2018v2p5VSmu
    self.out.idDeepTau2018v2p5VSjet_2[0]   = tau.idDeepTau2018v2p5VSjet

    
    # GENERATOR
    if self.ismc:
      self.out.genmatch_1[0]     = electron.genPartFlav
      self.out.genmatch_2[0]     = tau.genPartFlav
      pt, eta, phi, status       = matchgenvistau(event,tau)
      self.out.genvistaupt_2[0]  = pt
      self.out.genvistaueta_2[0] = eta
      self.out.genvistauphi_2[0] = phi
      self.out.gendm_2[0]        = status
      #if self.dozpt:
      #  self.out.mutaufilter[0]  = filtermutau(event)
    
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
      
      # ELECTRON WEIGHTS
      self.out.trigweight[0]              = self.eleSFs.getTriggerSF(electron.pt,abs(electron.eta))
      self.out.idisoweight_1[0]           = self.eleSFs.getIdIsoSF(electron.pt,abs(electron.eta))

      #print("eta: ", electron.eta)
      #print("pt: ",  electron.pt)
      #print("idiso sf: ", self.out.idisoweight_1[0])
      #print("trig sf: ", self.out.trigweight[0])
      #print("sf wo abs: ", self.eleSFs.getIdIsoSF(electron.pt,electron.eta))
      #print("sf wo abs: ", self.eleSFs.getIdIsoSF(electron.pt,abs(electron.eta)))

            
      # DEFAULTS
      self.out.idweight_2[0]          = 1.
      #self.out.idweight_dm_2[0]       = 1.
      #self.out.idweight_medium_2[0]   = 1.
      
      self.out.ltfweight_2[0]         = 1.
      if self.dosys:
        self.out.idweightUp_2[0]      = 1.
        self.out.idweightDown_2[0]    = 1.
        #self.out.idweightUp_dm_2[0]   = 1.
        #self.out.idweightDown_dm_2[0] = 1.
        self.out.ltfweightUp_2[0]     = 1.
        self.out.ltfweightDown_2[0]   = 1.
      
      # WEIGHTS

      self.out.weight[0]              = self.out.genweight[0]*self.out.puweight[0]*self.out.trigweight[0]*self.out.idisoweight_1[0] #*self.out.idisoweight_2[0]
    elif self.isembed:
      ###self.applyCommonEmbdedCorrections(event,jets,jetIds50,met,njets_vars,met_vars)
      self.out.genweight[0]           = event.genWeight
      self.out.trackweight[0]         = 0.975 if tau.decayMode==0 else 1.0247 if tau.decayMode==1 else 0.927 if tau.decayMode==10 else 0.974 if tau.decayMode==11 else 1.0
     
        
    # MET & DILEPTON VARIABLES
    self.fillMETAndDiLeptonBranches(event,electron,tau,met,met_vars)
    if self.Zres:
      print("---")
      print(self.out.m_vis[0])
      self.out.m_vis[0]   = 91.19 + (self.Zres)*(self.out.m_vis[0]-91.19) 
      print(self.out.m_vis[0])
    
    self.out.fill()
    return True
    
