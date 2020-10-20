# Author: Izaak Neutelings (October 2020)
# Description: Simple module to study jet to tau fakes
from ROOT import TFile, TTree, TH1D, gDirectory
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class ModuleJetTauFakeSimple(Module):
  
  def __init__(self,fname,**kwargs):
    self.fname = fname
  
  def beginJob(self):
    """Prepare output analysis tree and cutflow histogram."""
    
    # FILE
    self.outfile = TFile(self.fname,'RECREATE')
    self.njet     = TH1D('njet','Number of jets',15,0,15)
    self.njtf     = TH1D('njtf','Number of j #rightarrow #tau_{h} fakes',10,0,10)
    self.flav_all = TH1D('flav_all','jet flav;Jet parton flavor;Number of jets',25,0,25)
    self.flav_jtf = TH1D('flav_jtf',"jet flav of j #to #tau_{h} fake (Medium VSjet);Jet parton flavor;Number of j #rightarrow #tau_{h}",25,0,25)
    self.flav_eff = TH1D('flav_eff',"j #rightarrow #tau_{h} fake rate (Medium VSjet);Jet parton flavor; Medium VSjet j #rightarrow #tau_{h} fake rate",25,0,25)
    self.jet      = TTree('jet','jet') # save per jet
    self.jtf      = TTree('jtf','jtf') # save per j -> tauh fake
    
    # JET BRANCHES
    self.jet_pt    = np.zeros(1,dtype='f')
    self.jet_eta   = np.zeros(1,dtype='f')
    self.jet_flav  = np.zeros(1,dtype='i')
    self.jet_VSjet = np.zeros(1,dtype='i')
    self.jet_VSmu  = np.zeros(1,dtype='i')
    self.jet_VSe   = np.zeros(1,dtype='f')
    self.jet_tpt   = np.zeros(1,dtype='f')
    self.jet_teta  = np.zeros(1,dtype='f')
    self.jet_dR    = np.zeros(1,dtype='f')
    self.jet.Branch('pt',    self.jet_pt,    'pt/F'   ).SetTitle("jet pt")
    self.jet.Branch('eta',   self.jet_eta,   'eta/F'  ).SetTitle("jet eta")
    self.jet.Branch('flav',  self.jet_flav,  'flav/I' ).SetTitle("jet parton flavor")
    self.jet.Branch('VSjet', self.jet_VSjet, 'VSjet/I').SetTitle("tau DeepTauVSjet")
    self.jet.Branch('VSmu',  self.jet_VSmu,  'VSmu/I' ).SetTitle("tau DeepTauVSmu")
    self.jet.Branch('VSe',   self.jet_VSe,   'VSe/I'  ).SetTitle("tau DeepTauVSe")
    self.jet.Branch('tpt',   self.jet_tpt,   'tpt/F'  ).SetTitle("tau pt")
    self.jet.Branch('teta',  self.jet_teta,  'teta/F' ).SetTitle("tau eta")
    self.jet.Branch('dR',    self.jet_dR,    'dR/F'   ).SetTitle("DeltaR(jet,tau)")
    
    # TAU BRANCHES
    self.jtf_pt    = np.zeros(1,dtype='f')
    self.jtf_eta   = np.zeros(1,dtype='f')
    self.jtf_VSjet = np.zeros(1,dtype='i')
    self.jtf_VSmu  = np.zeros(1,dtype='f')
    self.jtf_VSe   = np.zeros(1,dtype='f')
    self.jtf_jpt   = np.zeros(1,dtype='f')
    self.jtf_jeta  = np.zeros(1,dtype='f')
    self.jtf_jflav = np.zeros(1,dtype='i')
    self.jtf_dR    = np.zeros(1,dtype='f')
    self.jtf.Branch('pt',    self.jtf_pt,    'pt/F'   ).SetTitle("tau pt")
    self.jtf.Branch('eta',   self.jtf_eta,   'eta/F'  ).SetTitle("tau eta")
    self.jtf.Branch('VSjet', self.jtf_VSjet, 'VSjet/I').SetTitle("tau DeepTauVSjet")
    self.jtf.Branch('VSmu',  self.jtf_VSmu,  'VSmu/I' ).SetTitle("tau DeepTauVSmu")
    self.jtf.Branch('VSe',   self.jtf_VSe,   'VSe/I'  ).SetTitle("tau DeepTauVSe")
    self.jtf.Branch('jpt',   self.jtf_jpt,   'jpt/F'  ).SetTitle("jet pt")
    self.jtf.Branch('jeta',  self.jtf_jeta,  'jeta/F' ).SetTitle("jet eta")
    self.jtf.Branch('jflav', self.jtf_jflav, 'jflav/I').SetTitle("jet parton flavor")
    self.jtf.Branch('dR',    self.jtf_dR,    'dR/F'   ).SetTitle("DeltaR(jet,tau)")
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.flav_eff.Add(self.flav_jtf)
    self.flav_eff.Divide(self.flav_all)
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    
    # COLLECTIONS
    taus  = Collection(event,'Tau')
    jets  = Collection(event,'Jet')
    
    # JETS
    njets = 0
    for jet in jets:
      self.jet_pt[0]   = jet.pt
      self.jet_eta[0]  = jet.eta
      self.jet_flav[0] = jet.partonFlavour
      njets += 1
      self.flav_all.Fill(jet.partonFlavour)
      for tau in taus:
        if tau.pt<20: continue
        if abs(tau.eta)>2.4: continue
        if tau.idDeepTau2017v2p1VSjet<1: continue # require loosest WP
        if tau.DeltaR(jet)>0.3: continue
        self.jet_tpt[0]   = tau.pt 
        self.jet_teta[0]  = tau.eta
        self.jet_VSjet[0] = tau.idDeepTau2017v2p1VSjet
        self.jet_VSmu[0]  = tau.idDeepTau2017v2p1VSmu
        self.jet_VSe[0]   = tau.idDeepTau2017v2p1VSe
        self.jet_dR[0]    = tau.DeltaR(jet)
        if tau.idDeepTau2017v2p1VSjet>=16: # require Medium WP
          self.flav_jtf.Fill(jet.partonFlavour)
        break
      else: # if not jet-tau match found
        self.jet_tpt[0]   = -9
        self.jet_teta[0]  = -9 
        self.jet_VSjet[0] = -1
        self.jet_VSmu[0]  = -1
        self.jet_VSe[0]   = -1
        self.jet_dR[0]    = -1
      self.jet.Fill() # save per j -> tauh
    self.njet.Fill(njets) # per event
    
    # JET -> TAU FAKES
    njtfs = 0
    for tau in taus:
      if tau.genPartFlav>0: continue # only save j -> tauh fakes
      if tau.pt<20: continue
      if abs(tau.eta)>2.4: continue
      #if abs(tau.dz)>0.2: continue
      if tau.idDeepTau2017v2p1VSjet<1: continue # require loosest WP
      self.jtf_pt[0]    = tau.pt
      self.jtf_eta[0]   = tau.eta
      self.jtf_VSjet[0] = tau.idDeepTau2017v2p1VSjet
      self.jtf_VSmu[0]  = tau.idDeepTau2017v2p1VSmu
      self.jtf_VSe[0]   = tau.idDeepTau2017v2p1VSe
      if 0<=tau.jetIdx<event.nJet:
        jet = jets[tau.jetIdx]
        self.jtf_jpt[0]   = jet.pt  
        self.jtf_jeta[0]  = jet.eta 
        self.jtf_jflav[0] = jet.partonFlavour
        self.jtf_dR[0]    = jet.DeltaR(tau)
      else:
        self.jtf_jpt[0]   = -9
        self.jtf_jeta[0]  = -9 
        self.jtf_jflav[0] = -1
        self.jtf_dR[0]    = -1
      self.jtf.Fill() # save per j -> tauh
      njtfs += 1
    self.njtf.Fill(njtfs) # per event
    
    return njets>0
