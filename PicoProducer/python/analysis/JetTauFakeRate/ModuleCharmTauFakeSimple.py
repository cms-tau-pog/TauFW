# Author: Izaak Neutelings (October 2020)
# Description: Simple module to study jet to tau fakes
from ROOT import TFile, TTree, TH1D, gDirectory
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.analysis.utils import dumpgenpart

class ModuleCharmTauFakeSimple(Module):
  
  def __init__(self,fname,**kwargs):
    self.fname = fname
  
  def beginJob(self):
    """Prepare output analysis tree and cutflow histogram."""
    
    # FILE
    self.outfile = TFile(self.fname,'RECREATE')
    self.njet      = TH1D('njet','Number of jets (p_{T}>20, |#eta|<2.4)',15,0,15)
    self.njtf      = TH1D('njtf','Number of j #rightarrow #tau_{h} fakes',10,0,10)
    self.pflav_all = TH1D('pflav_all','Jet parton flav;Jet parton flavor;Number of jets',25,0,25)
    self.pflav_jtf = TH1D('pflav_jtf',"Jet parton flav of j #rightarrow #tau_{h} fake (Medium VSjet, VVVLoose VSe, VLoose VSmu);Jet parton flavor;Number of j #rightarrow #tau_{h}",25,0,25)
    self.pflav_eff = TH1D('pflav_eff',"j #rightarrow #tau_{h} fake rate (Medium VSjet, VVVLoose VSe, VLoose VSmu);Jet parton flavor; Medium VSjet j #rightarrow #tau_{h} fake rate",25,0,25)
    self.hflav_all = TH1D('hflav_all','Jet hadron flav;Jet hadron flavor;Number of jets',8,0,8)
    self.hflav_jtf = TH1D('hflav_jtf',"Jet hadron flav of j #rightarrow #tau_{h} fake (Medium VSjet, VVVLoose VSe, VLoose VSmu);Jet hadron flavor;Number of j #rightarrow #tau_{h}",8,0,8)
    self.hflav_eff = TH1D('hflav_eff',"j #rightarrow #tau_{h} fake rate (Medium VSjet, VVVLoose VSe, VLoose VSmu);Jet hadron flavor; Medium VSjet j #rightarrow #tau_{h} fake rate",8,0,8)
    self.jet       = TTree('jet','jet') # save per jet
    self.jtf       = TTree('jtf','jtf') # save per j -> tauh fake
    
    # JET BRANCHES
    self.jet_pt    = np.zeros(1,dtype='f')
    self.jet_eta   = np.zeros(1,dtype='f')
    self.jet_pflav = np.zeros(1,dtype='i')
    self.jet_hflav = np.zeros(1,dtype='i')
    self.jet_tpt   = np.zeros(1,dtype='f')
    self.jet_teta  = np.zeros(1,dtype='f')
    self.jet_tdm   = np.zeros(1,dtype='f')
    self.jet_VSjet = np.zeros(1,dtype='i')
    self.jet_VSmu  = np.zeros(1,dtype='i')
    self.jet_VSe   = np.zeros(1,dtype='f')
    self.jet_dR    = np.zeros(1,dtype='f')
    self.jet.Branch('pt',    self.jet_pt,    'pt/F'   ).SetTitle("jet pt")
    self.jet.Branch('eta',   self.jet_eta,   'eta/F'  ).SetTitle("jet eta")
    self.jet.Branch('pflav', self.jet_pflav, 'pflav/I').SetTitle("jet parton flavor")
    self.jet.Branch('hflav', self.jet_hflav, 'hflav/I').SetTitle("jet hadron flavor")
    self.jet.Branch('tpt',   self.jet_tpt,   'tpt/F'  ).SetTitle("matched tau pt")
    self.jet.Branch('teta',  self.jet_teta,  'teta/F' ).SetTitle("matched tau eta")
    self.jet.Branch('tdm',   self.jet_tdm,   'tdm/F'  ).SetTitle("matched tau decay mode")
    self.jet.Branch('VSjet', self.jet_VSjet, 'VSjet/I').SetTitle("matched tau DeepTauVSjet")
    self.jet.Branch('VSmu',  self.jet_VSmu,  'VSmu/I' ).SetTitle("matched tau DeepTauVSmu")
    self.jet.Branch('VSe',   self.jet_VSe,   'VSe/I'  ).SetTitle("matched tau DeepTauVSe")
    self.jet.Branch('dR',    self.jet_dR,    'dR/F'   ).SetTitle("DeltaR(jet,tau)")
    
    # TAU BRANCHES
    self.jtf_pt    = np.zeros(1,dtype='f')
    self.jtf_eta   = np.zeros(1,dtype='f')
    self.jtf_dm    = np.zeros(1,dtype='i')
    self.jtf_VSjet = np.zeros(1,dtype='i')
    self.jtf_VSmu  = np.zeros(1,dtype='f')
    self.jtf_VSe   = np.zeros(1,dtype='f')
    self.jtf_jpt   = np.zeros(1,dtype='f')
    self.jtf_jeta  = np.zeros(1,dtype='f')
    self.jtf_pflav = np.zeros(1,dtype='i')
    self.jtf_hflav = np.zeros(1,dtype='i')
    self.jtf_dR    = np.zeros(1,dtype='f')
    self.jtf.Branch('pt',    self.jtf_pt,    'pt/F'   ).SetTitle("tau pt")
    self.jtf.Branch('eta',   self.jtf_eta,   'eta/F'  ).SetTitle("tau eta")
    self.jtf.Branch('dm',    self.jtf_dm,    'dm/I'   ).SetTitle("tau decay mode")
    self.jtf.Branch('VSjet', self.jtf_VSjet, 'VSjet/I').SetTitle("tau DeepTauVSjet")
    self.jtf.Branch('VSmu',  self.jtf_VSmu,  'VSmu/I' ).SetTitle("tau DeepTauVSmu")
    self.jtf.Branch('VSe',   self.jtf_VSe,   'VSe/I'  ).SetTitle("tau DeepTauVSe")
    self.jtf.Branch('jpt',   self.jtf_jpt,   'jpt/F'  ).SetTitle("matched jet pt")
    self.jtf.Branch('jeta',  self.jtf_jeta,  'jeta/F' ).SetTitle("matched jet eta")
    self.jtf.Branch('pflav', self.jtf_pflav, 'pflav/I').SetTitle("matched jet parton flavor")
    self.jtf.Branch('hflav', self.jtf_hflav, 'hflav/I').SetTitle("matched jet hadron flavor")
    self.jtf.Branch('dR',    self.jtf_dR,    'dR/F'   ).SetTitle("DeltaR(jet,tau)")
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.pflav_eff.Add(self.pflav_jtf)
    self.pflav_eff.Divide(self.pflav_all) # assuming each jet is reconstructed as a tau
    self.hflav_eff.Add(self.hflav_jtf)
    self.hflav_eff.Divide(self.hflav_all) # assuming each jet is reconstructed as a tau
    self.outfile.Write()
    self.outfile.Close()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    
    # COLLECTIONS
    ###taus = Collection(event,'Tau')
    ###jets = Collection(event,'Jet')
    genparts = Collection(event,'GenPart')
    #tauvis = Collection(event,'GenVisTau')
    
    # MATCH
    # https://pdg.lbl.gov/2019/reviews/rpp2019-rev-monte-carlo-numbering.pdf
    print '-'*80
    D_pids = [4,411,421,413,423,415,425,431,433,435,10411,10421,10413,10423,]
    Dparts = [ ]
    for genpart in genparts:
      pid = abs(genpart.pdgId)
      if pid in D_pids:
        dumpgenpart(genpart,genparts=genparts,flags=[7,8])
        Dparts.append(genpart)
    
    #### JETS
    ###njets = 0
    ###for jet in jets:
    ###  if jet.pt<20: continue
    ###  if abs(jet.eta)>2.4: continue
    ###  #rightarrowDO: count or remove jets matching with real gen-level tauh ?
    ###  self.jet_pt[0]    = jet.pt
    ###  self.jet_eta[0]   = jet.eta
    ###  self.jet_pflav[0] = jet.partonFlavour
    ###  self.jet_hflav[0] = jet.hadronFlavour
    ###  self.pflav_all.Fill(abs(jet.partonFlavour))
    ###  self.hflav_all.Fill(jet.hadronFlavour)
    ###  for tau in taus:
    ###    if tau.pt<20: continue
    ###    if abs(tau.eta)>2.4: continue
    ###    if tau.idDeepTau2017v2p1VSjet<1: continue # require loosest WP
    ###    if tau.DeltaR(jet)>0.3: continue
    ###    self.jet_tpt[0]   = tau.pt 
    ###    self.jet_teta[0]  = tau.eta
    ###    self.jet_tdm[0]   = tau.decayMode
    ###    self.jet_VSjet[0] = tau.idDeepTau2017v2p1VSjet
    ###    self.jet_VSmu[0]  = tau.idDeepTau2017v2p1VSmu
    ###    self.jet_VSe[0]   = tau.idDeepTau2017v2p1VSe
    ###    self.jet_dR[0]    = tau.DeltaR(jet)
    ###    if tau.idDeepTau2017v2p1VSe>0 and tau.idDeepTau2017v2p1VSmu>0 and tau.idDeepTau2017v2p1VSjet>=16: # require Medium WP
    ###      self.pflav_jtf.Fill(abs(jet.partonFlavour))
    ###      self.hflav_jtf.Fill(jet.hadronFlavour)
    ###    break
    ###  else: # if not jet-tau match found
    ###    self.jet_tpt[0]   = -9
    ###    self.jet_teta[0]  = -9 
    ###    self.jet_tdm[0]   = -1
    ###    self.jet_VSjet[0] = -1
    ###    self.jet_VSmu[0]  = -1
    ###    self.jet_VSe[0]   = -1
    ###    self.jet_dR[0]    = -1
    ###  self.jet.Fill() # save per j -> tauh
    ###  njets += 1
    ###self.njet.Fill(njets) # per event
    ###
    #### JET -> TAU FAKES
    ###njtfs = 0
    ###for tau in taus:
    ###  if tau.genPartFlav>0: continue # only save j -> tauh fakes
    ###  if tau.pt<20: continue
    ###  if abs(tau.eta)>2.4: continue
    ###  #if abs(tau.dz)>0.2: continue
    ###  #if tau.idDeepTau2017v2p1VSe<1: continue # require loosest WP
    ###  #if tau.idDeepTau2017v2p1VSmu<1: continue # require loosest WP
    ###  if tau.idDeepTau2017v2p1VSjet<1: continue # require loosest WP
    ###  self.jtf_pt[0]    = tau.pt
    ###  self.jtf_eta[0]   = tau.eta
    ###  self.jtf_dm[0]    = tau.decayMode
    ###  self.jtf_VSjet[0] = tau.idDeepTau2017v2p1VSjet
    ###  self.jtf_VSmu[0]  = tau.idDeepTau2017v2p1VSmu
    ###  self.jtf_VSe[0]   = tau.idDeepTau2017v2p1VSe
    ###  if 0<=tau.jetIdx<event.nJet:
    ###    jet = jets[tau.jetIdx]
    ###    self.jtf_jpt[0]   = jet.pt
    ###    self.jtf_jeta[0]  = jet.eta
    ###    self.jtf_pflav[0] = jet.partonFlavour
    ###    self.jtf_hflav[0] = jet.hadronFlavour
    ###    self.jtf_dR[0]    = jet.DeltaR(tau)
    ###  else:
    ###    self.jtf_jpt[0]   = -9
    ###    self.jtf_jeta[0]  = -9 
    ###    self.jtf_pflav[0] = -9
    ###    self.jtf_hflav[0] = -1
    ###    self.jtf_dR[0]    = -1
    ###  self.jtf.Fill() # save per j -> tauh
    ###  njtfs += 1
    ###self.njtf.Fill(njtfs) # per event
    
    ###return njets>0 # just for counting events
