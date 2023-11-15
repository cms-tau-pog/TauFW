#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2020)
# Description:
#   Simple example of gen-level study of LQ samples.
#   This analysis module selects interesting particles for various LQ processes,
#   and creates an output file with a single flat tree for several kinematic variables.
# Instructions to run standalone:
#   python3 python/analysis/LQ/ModuleGenLQ.py --lq t -t _nonres -n 10000
# Instructions to run with pico.py:
#   pico.py channel lq python/analysis/LQ/ModuleGenLQ.py
#   pico.py era 2018 samples/LQ/samples_2018.py
#   pico.py run -c lq -y 2018 -s SLQ-t_M2000 -m 10000 -n10
# Sources:
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc106Xul18_doc.html#GenPart
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/genparticles_cff.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/LHETablesProducer.cc
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/examples/exampleGenDump.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/GenDumper.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/LQ/ModuleGenLQ.py
#   https://pdg.lbl.gov/2023/reviews/rpp2022-rev-monte-carlo-numbering.pdf (PDG ID)
#   https://pythia.org/latest-manual/ParticleProperties.html (Pythia particle status)
from __future__ import print_function # for python3 compatibility
import os
from math import sqrt, cos
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import TLorentzVector
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.processors import moddir
from TauFW.PicoProducer.analysis.utils import getmother, getlastcopy, dumpgenpart, getprodchain, getdecaychain, deltaPhi
#import PhysicsTools.NanoAODTools.postprocessing.framework.datamodel as datamodel
#datamodel.statusflags['isHardPrompt'] = datamodel.statusflags['isPrompt'] + datamodel.statusflags['fromHardProcess'] # define shortcut
#datamodel.statusflags['isTauFSR'] = datamodel.statusflags['isTauDecayProduct'] + datamodel.statusflags['isDirectHadronDecayProduct'] # define shortcut
branchsel = os.path.join(moddir,"keep_and_drop_gen.txt")


def getdRmin(part,oparts):
  """Find DeltaR with closest particle."""
  dRmin = 10 if oparts else -1
  for opart in oparts:
    dR = part.DeltaR(opart)
    if dR<dRmin:
      dRmin = dR
  return dRmin
  

def getdmbin(dm):
  """Get hadronic decay mode"""
  if dm<3: return dm # one-prong, 0-2 pi^0
  elif dm==10: return 3 # three-prong, no pi^0
  elif dm==11: return 4 # three-prong, 2 pi^0
  return 5 # other (everything else)
  

class GenVisTau:
  """Class to contain visible decay products from both leptonic and hadronic tau decay.
  Note nanoAOD's GenVisTau collection only includes hadronic decays."""
  def __init__(self,genpart,tau=None,mother=None):
    self.settau(tau,mother) # set tau and tau's mother
    self.obj  = genpart
    self.p4   = genpart.p4() # total visible four-momentum (sum of visible decay products, incl. FSR within dR<0.4)
    if genpart._prefix=='GenVisTau_': # GenVisTau object (hadronic decay)
      self.dm = 3+getdmbin(genpart.status) # decay mode (hadronic >= 3)
    else: # assume GenPart object is electron or muon
      self.dm = 1 if abs(genpart.pdgId)==11 else 2 # decay mode: 1 (bin 2) = electron; 2 (bin 3) = muon
  
  def settau(self,tau,mother=None):
    """Set mother tau and tau's mother."""
    self.tau = tau # mother tau
    self.mother = mother if mother!=None else tau.mother if tau!=None else 0 # PDG ID of tau's mother, default: 0 (bin 1) = no daughter found
    return mother
  
  @property
  def pt(self):
    return self.p4.Pt()
  
  @property
  def eta(self):
    return self.p4.Eta()
  
  @property
  def phi(self):
    return self.p4.Phi()
  
  def mt(self,opt,ophi):
    """Transverse mass with some other object."""
    # https://en.wikipedia.org/wiki/Transverse_mass#Transverse_mass_in_two-particle_systems
    return sqrt( 2*self.p4.Pt()*opt*(1-cos(self.p4.Phi()-ophi)) )
  

# MAIN PHYSICAL ANALYSIS MODULE
class ModuleGenLQ(Module):
  """Find interesting particles for gen studies of LQ -> btau:
  tau leptons and its visible decays, bottom quarks, gen. jets, ..."""
  
  def __init__(self,fname,**kwargs):
    
    # CREATE OUTPUT FILE with single tree
    self.out = TreeProducer(fname,self,**kwargs)
    self.branchsel = branchsel # disable unneeded branches for faster processing
    
    # ADD CUTS TO CUTFLOW
    self.out.cutflow.addcut('nocut',"No cut")
    self.out.cutflow.addcut('notop',"No top quarks in the event")
    
    # ADD HISTOGRAMS
    dmlabs     = ['None','Electron','Muon','Hadronic'] # axis labels for tau decay modes
    dmlabs_all = ['None','e^{#pm}','#mu^{#pm}', # leptonic decays (1=electron, 2=muon)
                  'h^{#pm}','h^{#pm}#pi^{0}','h^{#pm}#pi^{0}#pi^{0}', # one-prong
                  'h^{#pm}h^{#mp}h^{#pm}','h^{#pm}h^{#mp}h^{#pm}#pi^{0}','Other'] # axis labels for hadronic tau decay modes
    self.out.addHist('mass_lq',"LQ mass",2500,0,2500)
    self.out.addHist('dR_tj',"#DeltaR between #tau and closest jet",60,-1,5) # to study optimal dR cut
    self.out.addHist('dR_jt',"#DeltaR between jet and closest #tau",60,-1,5) # to study optimal dR cut
    self.out.addHist('dR_vt',"#DeltaR between visible #tau (hadronic decay) and closest tau",100,0,5)
    self.out.addHist('dR_lt',"#DeltaR between #tau and its daughter lepton",60,0,3)
    self.out.addHist('dR_tp',"#DeltaR between final #tau and its FSR photon",100,0,3) # to study FSR
    self.out.addHist('dR_vp',"#DeltaR between visible #tau and its FSR photon",100,0,3) # to study FSR
    self.out.addHist('dptvis_fsr',"(p_{T,vis}^{after} #minus p_{T,vis}^{before})/p_{T,vis}^{before} between tau and its FSR photon (#DeltaR<0.3)",100,-0.5,0.7) # to study FSR
    self.out.addHist('dptvis_lep',"(p_{T}^{vis} #minus p_{T}^{#tau})/p_{T}^{#tau} (leptonic decay, p_{T} > 20 GeV)",100,-1.2,0.8) # to study tau decay
    self.out.addHist('dptvis_had',"(p_{T}^{vis} #minus p_{T}^{#tau})/p_{T}^{#tau} (hadronic decay, p_{T} > 20 GeV)",100,-1.2,0.8) # to study tau decay
    self.out.addHist('pt_tau_vs_vis_had',"Leptonic decay;p_{T}^{#tau};p_{T}^{vis}",80,0,800,80,0,800) # to study tau decay
    self.out.addHist('pt_tau_vs_vis_lep',"Leptonic decay;p_{T}^{#tau};p_{T}^{vis}",80,0,800,80,0,800) # to study tau decay
    self.out.addHist('dptmiss_nu',"(p_{T,#nu}^{miss} #minus p_{T,gen}^{miss})/p_{T,gen}^{miss}",100,-0.6,0.6) # to study gen-level MET
    self.out.addHist('dphimiss_nu',"#phi_{#nu}^{miss} #minus #phi_{gen}^{miss}",100,-4,4) # to study gen-level MET
    self.out.addHist('tau_dm',"#tau lepton decay modes",4,0,4,xlabs=dmlabs) # to study tau lepton decay (compare to PDG)
    self.out.addHist('tau_dm_all',"Hadronic decay modes of #tau lepton (p_{T} > 20 GeV)",9,0,9,xlabs=dmlabs_all) # to study tau lepton decay (compare to PDG)
    self.out.addHist('tau_dm2D',"#tau decay modes;Leading #tau;Subleading #tau",
                     4,0,4,4,0,4,xlabs=dmlabs,ylabs=dmlabs,option='COLZ TEXT44')
    
    # ADD BRANCHES
    self.out.addBranch('genweight',      'f', title="Generator weight")
    self.out.addBranch('nlqs',           'i', title="Number of LQs")
    self.out.addBranch('nelecs',         'i', title="Number of electrons")
    self.out.addBranch('nmuons',         'i', title="Number of muons")
    self.out.addBranch('ntaus',          'i', title="Number of tau leptons")
    self.out.addBranch('ntaus20',        'i', title="Number of tau leptons (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nleptaus',       'i', title="Number of leptonic tau decays")
    self.out.addBranch('nleptaus20',     'i', title="Number of leptonic tau decays (pTvis > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nhadtaus',       'i', title="Number of hadronic tau decays (pTvis > 10 GeV)")
    self.out.addBranch('nhadtaus20',     'i', title="Number of hadronic tau decays (pTvis > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nvistaus',       'i', title="Number of visible tau decay products (pT > 10 GeV for had.)") # default cut
    self.out.addBranch('nvistaus20',     'i', title="Number of visible tau decay products (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nvistaus50',     'i', title="Number of visible tau decay products (pT > 50 GeV, |eta|<2.5)")
    self.out.addBranch('nnus',           'i', title="Number of neutrinos")
    self.out.addBranch('ntnus',          'i', title="Number of tau neutrinos")
    self.out.addBranch('nbots',          'i', title="Number of bottom quarks")
    self.out.addBranch('nbots20',        'i', title="Number of bottom quarks (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('ntops',          'i', title="Number of top quarks")
    self.out.addBranch('njets',          'i', title="Number of gen AK4 jets (no tau decays)")
    self.out.addBranch('nbjets',         'i', title="Number of gen AK4 b jets")
    self.out.addBranch('nbjets20',       'i', title="Number of gen AK4 b jets (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nbjets50',       'i', title="Number of gen AK4 b jets (pT > 50 GeV, |eta|<2.5)")
    self.out.addBranch('ncjets20',       'i', title="Number of gen AK4 jets (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('ncjets50',       'i', title="Number of gen AK4 jets (pT > 50 GeV, |eta|<2.5)")
    self.out.addBranch('nfjets20',       'i', title="Number of gen AK4 jets (pT > 20 GeV, 2.5<|eta|<4.7)")
    self.out.addBranch('nfjets50',       'i', title="Number of gen AK4 jets (pT > 50 GeV, 2.5<|eta|<4.7)")
    
    # ADD BRANCHES for RECONSTRUCTED VARIABLES
    self.out.addBranch('dR_tt',          'f', title="DeltaR between leading tau leptons")
    self.out.addBranch('dRvis_tt',       'f', title="DeltaR between visible decays of leading tau leptons")
    self.out.addBranch('dR_ttvis',       'f', title="DeltaR between visible tau leptons")
    self.out.addBranch('dR_bb',          'f', title="DeltaR between bottom quarks")
    self.out.addBranch('m_lq',           'f', title="LQ mass")
    self.out.addBranch('m_tt',           'f', title="Invariant mass between two leading taus")
    self.out.addBranch('mvis_tt',        'f', title="Visible mass between two leading taus")
    self.out.addBranch('pt_tt',          'f', title="pT of two leading taus")
    self.out.addBranch('ptvis_tt',       'f', title="Visible pT of two leading taus")
    self.out.addBranch('dphi_vistau',    'f', title="DeltaPhi between leading vis. tau")
    self.out.addBranch('ht',             'f', title="Sum of hadronic transverse energy (no taus)")
    self.out.addBranch('met',            'f', title="MET") # gen-level missing transverse energy
    self.out.addBranch('metphi',         'f', title="MET phi") # gen-level missing transverse energy
    
    # ADD BRANCHES for LQs
    self.out.addBranch('pt_lq1',         'f', title="pT of the leading LQ")
    self.out.addBranch('pt_lq2',         'f', title="pT of the subleading LQ") # for pair production only
    self.out.addBranch('dau1_lq1',       'i', title="PDG ID of daughter 1 of leading LQ")
    self.out.addBranch('dau1_lq2',       'i', title="PDG ID of daughter 2 of leading LQ")
    self.out.addBranch('dau2_lq1',       'i', title="PDG ID of daughter 1 of subleading LQ") # for pair production only
    self.out.addBranch('dau2_lq2',       'i', title="PDG ID of daughter 2 of subleading LQ") # for pair production only
    
    # ADD BRANCHES for TAU DECAYS
    self.out.addBranch('pt_tau1',        'f', title="pT of leading tau")
    self.out.addBranch('pt_tau2',        'f', title="pT of subleading tau")
    self.out.addBranch('ptvis_tau1',     'f', title="Visible pT of leading tau")
    self.out.addBranch('ptvis_tau2',     'f', title="Visible pT of subleading tau")
    self.out.addBranch('eta_tau1',       'f', title="eta of leading tau")
    self.out.addBranch('eta_tau2',       'f', title="eta of subleading tau")
    self.out.addBranch('moth_tau1',      'i', title="Mother of leading tau")
    self.out.addBranch('moth_tau2',      'i', title="Mother of subleading tau")
    self.out.addBranch('dm_tau1',        'i', title="Decay mode of leading tau")
    self.out.addBranch('dm_tau2',        'i', title="Decay mode of subleading tau")
    
    # ADD BRANCHES for VISIBLE TAU DECAYS
    self.out.addBranch('pt_vistau1',     'f', title="pT of leading tau")
    self.out.addBranch('pt_vistau2',     'f', title="pT of subleading vis. tau")
    self.out.addBranch('eta_vistau1',    'f', title="eta of leading tau")
    self.out.addBranch('eta_vistau2',    'f', title="eta of subleading vis. tau")
    self.out.addBranch('phi_vistau1',    'f', title="phi of leading tau")
    self.out.addBranch('phi_vistau2',    'f', title="phi of subleading vis. tau")
    self.out.addBranch('moth_vistau1',   'i', title="Mother of leading vis. tau")
    self.out.addBranch('moth_vistau2',   'i', title="Mother of subleading vis. tau")
    self.out.addBranch('dm_vistau1',     'i', title="Decay mode of leading vis. tau")
    self.out.addBranch('dm_vistau2',     'i', title="Decay mode of subleading vis. tau")
    self.out.addBranch('mt_vistau1',     'f', title="Transverse mass between MET & leading vis. tau")
    self.out.addBranch('mt_vistau2',     'f', title="Transverse mass between MET & subleading vis. tau")
    
    # ADD BRANCHES for BOTTOM QUARKS
    self.out.addBranch('pt_bot1',        'f', title="pT of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('pt_bot2',        'f', title="pT of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('eta_bot1',       'f', title="eta of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('eta_bot2',       'f', title="eta of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('moth_bot1',      'i', title="Mother of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('moth_bot2',      'i', title="Mother of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    
    # ADD BRANCHES for AK4 GEN JET
    self.out.addBranch('pt_jet1',        'f', title="pT of leading gen jet")
    self.out.addBranch('pt_jet2',        'f', title="pT of subleading gen jet")
    self.out.addBranch('eta_jet1',       'f', title="eta of leading gen jet")
    self.out.addBranch('eta_jet2',       'f', title="eta of subleading gen jet")
    self.out.addBranch('flavor_jet1',    'i', title="flavor of leading gen jet")
    self.out.addBranch('flavor_jet2',    'i', title="flavor of subleading gen jet")
    self.out.addBranch('pt_bjet1',       'f', title="pT of leading gen b jet")
    self.out.addBranch('pt_bjet2',       'f', title="pT of subleading gen b jet")
    self.out.addBranch('eta_bjet1',      'f', title="eta of leading gen b jet")
    self.out.addBranch('eta_bjet2',      'f', title="eta of subleading gen b jet")
    
    # ADD ALIASES (to save disk space)
    self.out.setAlias('st',          "pt_tau1+pt_tau2+pt_jet1") # scalar sum pT with full tau
    self.out.setAlias('stmet',       "pt_tau1+pt_tau2+pt_jet1+met") # scalar sum pT with full tau
    self.out.setAlias('stvis',       "pt_vistau1+pt_vistau2+pt_jet1") # scalar sum pT (visible)
    self.out.setAlias('stmetvis',    "pt_vistau1+pt_vistau2+pt_jet1+met") # scalar sum pT (visible)
    self.out.setAlias('nleps',       "nelecs+nmuons") # all leptonic decays
    self.out.setAlias('njets20',     "nfjets20+ncjets20") # all jets with pT > 20 GeV, |eta|<4.7
    self.out.setAlias('njets50',     "nfjets50+ncjets50") # all jets with pT > 50 GeV, |eta|<4.7
    self.out.setAlias('nljets20',    "nfjets20+ncjets20-nbjets20") # number of light jets with pT > 20 GeV, |eta|<4.7
    self.out.setAlias('nljets50',    "nfjets50+ncjets50-nbjets50") # number of light jets with pT > 50 GeV, |eta|<4.7
    self.out.setAlias('ll',          "1<=dm_vistau1 && dm_vistau1<=2 && 1<=dm_vistau2 && dm_vistau2<=2 ") # fully leptonic tau decay
    self.out.setAlias('etau',        "(dm_vistau1==1 && dm_vistau2>=3) || (dm_vistau2==1 && dm_vistau1>=3)") # electronic tau decay
    self.out.setAlias('mutau',       "(dm_vistau1==2 && dm_vistau2>=3) || (dm_vistau2==2 && dm_vistau1>=3)") # muonic tau decay
    self.out.setAlias('ltau',        "((dm_vistau1==1||dm_vistau1==2) && dm_vistau2>=3) || ((dm_vistau2==1||dm_vistau2==2) && dm_vistau1>=3)") # semileptonic tau decay
    self.out.setAlias('tautau',      "dm_vistau1>=3 && dm_vistau2>=3") # fully hadronic tau decay
    self.out.setAlias('chi',         "exp(abs(eta_tau1-eta_tau2))")
    self.out.setAlias('chivis',      "exp(abs(eta_vistau1-eta_vistau2))")
    #self.out.setAlias('dphi_vistau', "ROOT::VecOps::DeltaPhi(phi_vistau1,phi_vistau2)") # fold with ROOT::VecOps::DeltaPhi
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    hist = self.out.hists['tau_dm_all']
    nall = hist.GetEntries()
    if nall>0:
      ntau = nall-hist.GetBinContent(1)
      print(f">>> Tau decays: {ntau} with pT > 20 GeV (assigned {100.0*ntau/nall:.1f}%)")
      if ntau>0:
        eff  = lambda n, N: (100.*n/N, 100.*sqrt((n/N)*(1.-n/N)/N)) # efficiency & uncertainty
        perc = lambda *l: "(%5.1f +-%4.1f )%%"%eff(sum(hist.GetBinContent(i) for i in l),ntau) # percentage
        print(f">>>   Leptonic:   {perc(2,3)}")
        print(f">>>     Electron: {perc(2)}")
        print(f">>>     Muon:     {perc(3)}")
        print(f">>>   Hadronic:   {perc(4,5,6,7,8,9)}")
        print(f">>>     1h:       {perc(4)}") # one-prong (one charged hadron)
        print(f">>>     1h+1pi0:  {perc(5)}")
        print(f">>>     1h+2pi0:  {perc(6)}")
        print(f">>>     3h:       {perc(7)}") # three-prong (three charged hadrons)
        print(f">>>     3h+1pi0:  {perc(8)}")
        print(f">>>     Other:    {perc(9)}")
    self.out.endJob()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('nocut')
    
    # PREPARE lists of selected gen-level particles
    elecs   = [ ] # electrons
    muons   = [ ] # muons
    leptaus = [ ] # leptons from tau decay
    hadtaus = [ ] # hadronic tau decays
    taus    = [ ] # tau leptons
    tnus    = [ ] # tau neutrinos
    nus     = [ ] # all neutrinos
    photons = [ ] # FSR photons from tau leptons
    bots    = [ ] # bottom quarks
    tops    = [ ] # top quarks
    jets    = [ ] # jets
    bjets   = [ ] # b jets
    cjets   = [ ] # central jets |eta|<2.5
    fjets   = [ ] # forward jets 2.5<|eta|<4.7
    vistaus = [ ] # visible tau decay products (visible four-momentum)
    lqs     = [ ] # LQs
    lqids   = [46,9000002,9000006] # PDG IDs of LQs in various MadGraph or Pythia generators
    p4_nu   = TLorentzVector() # four-momentum of all neutrinos (to compare to gen-level MET)
    #p4_met  = TLorentzVector() # four-momentum of gen-level MET
    #p4_met.SetPtEtaPhiE(event.GenMET_pt,0,event.GenMET_phi,event.GenMET_pt)
    
    # LOOP over gen-level particles
    #print('-'*80) # print to separate events during debugging
    genparts = Collection(event,'GenPart') # generator-level particles
    genjets  = Collection(event,'GenJet') # generator-level jets
    for part in genparts:
      pid = abs(part.pdgId) # remove charge sign
      #dumpgenpart(part,genparts=genparts) # print for debugging
      
      # LQ decay products
      for lq in lqs: # check if part is LQ decay product
        if lq._index==part.genPartIdxMother: # LQ is mother
          lq.decays.append(part.pdgId) # save PDG only
      
      # LAST COPY
      if not part.statusflag('isLastCopy'):
        continue # only analyze last copies
      
      # LQ particle
      if pid in lqids: # this particle is a LQ
        #if part.status<60:
        #  continue # about to decay (i.e. last copy)
        part.decays = [ ]
        lqs.append(part)
      
      # BOTTOM quark
      elif pid==5 and part.status!=21 and abs(part.eta)<10: # remove initial state b quark (from hard process)
        part.mother = getmother(part,genparts).pdgId # get mother PDG ID
        bots.append(part)
      
      # TOP quark
      elif pid==6:
        tops.append(part)
      
      # ELECTRON
      elif pid==11:
        elecs.append(part)
        if part.statusflag('isTauDecayProduct'):
          #print(getprodchain(part,genparts))
          #dumpgenpart(part,genparts,flags=['isTauDecayProduct','isPromptTauDecayProduct','isDirectTauDecayProduct']) # print for debugging
          moth = getmother(part,genparts) # get mother tau
          if abs(moth.pdgId)==15: # primary tau decay product (e.g. not from hadron decays)
            #print(getdecaychain(moth,genparts)) # print for debugging
            moth.vistau = GenVisTau(part,moth) # assign visible daughter to tau
            self.out.fill('dR_lt',moth.DeltaR(part)) # DeltaR between tau and its daughter lepton
            leptaus.append(part)
            vistaus.append(moth.vistau)
      
      # MUON
      elif pid==13:
        muons.append(part)
        if part.statusflag('isTauDecayProduct'):
          #dumpgenpart(part,genparts,flags=['isTauDecayProduct','isPromptTauDecayProduct','isDirectTauDecayProduct']) # print for debugging
          moth = getmother(part,genparts) # get mother tau
          if abs(moth.pdgId)==15: # primary tau decay product (e.g. not from hadron decays)
            moth.vistau = GenVisTau(part,moth) # assign visible daughter to tau
            self.out.fill('dR_lt',moth.DeltaR(part)) # DeltaR between tau and its daughter lepton
            leptaus.append(part)
            vistaus.append(moth.vistau)
      
      # TAU lepton
      elif pid==15:
        part.mother = getmother(part,genparts).pdgId # get mother PDG ID
        part.vistau = None # visible pT, default: -2 = no visible decay product found
        taus.append(part)
        self.out.fill('dR_tj',getdRmin(part,genjets)) # DeltaR between tau and closest jet
      
      # ELECTRON or MUON neutrinos
      elif pid==12 or pid==14:
        p4_nu += part.p4()
        nus.append(part)
      
      # TAU neutrinos
      elif pid==16:
        p4_nu += part.p4()
        tnus.append(part)
        nus.append(part)
      
      # PHOTONS (FSR from tau)
      elif pid==22:
        moth = getmother(part,genparts) # get mother tau
        if abs(moth.pdgId)==15: # FSR from tau
          lasttau = getlastcopy(moth,genparts) # get last copy of tau (after all FSR)
          part.mother = moth
          part.tau = lasttau # save for matching with other taus later
          photons.append(part) # save for adding to total visible momentum later
          #print(getprodchain(part,genparts))
          #dumpgenpart(part,genparts,flags=['isTauDecayProduct','isPromptTauDecayProduct','isDirectTauDecayProduct','isDirectHadronDecayProduct']) # print for debugging
    
    # ADD FSR photons to leptonic decay (assume GenVisTau is done correctly)
    for vistau in vistaus:
      if vistau.dm not in [1,2]: continue
      for photon in photons:
        if vistau.tau==photon.tau: # photon is FSR of this last-copy tau
          dR    = photon.DeltaR(vistau.tau)
          dRvis = photon.DeltaR(vistau.p4)
          self.out.fill('dR_tp',dR) # DeltaR between final tau and FSR photon
          self.out.fill('dR_vp',dRvis) # DeltaR between visible tau and FSR photon
          if dRvis<0.3: # only add photon if it falls within dR=0.3 cone like in tau reco
            ptvisold = vistau.pt # pT before adding FSR
            vistau.p4 += photon.p4() # add to visible tau momentum (charged lepton)
            self.out.fill('dptvis_fsr',(vistau.pt-ptvisold)/ptvisold) # to study FSR
    
    # VISIBLE DECAY PRODUCTS from HADRONIC TAU DECAYS (gen-level)
    # Because neutrinos carry away energy & momentum,
    # we need the four-momentum of the visible decay
    # products of the selected tau particles
    # Note: pt > 10 GeV cut is applied to the GenVisTau collection
    # Note: GenVisTau.genPartIdxMother is inaccurate...
    for vistau_ in Collection(event,'GenVisTau'): # hadronic decays only
      tmoth = None # mother tau
      dRmin = 10. # DeltaR with closest "full" tau lepton
      vistau = GenVisTau(vistau_) # convert to custom GenVisTau object
      for tau in taus: # gen-level taus
        dR = tau.DeltaR(vistau.p4)
        if dR<dRmin: # match with "full" tau lepton
          dRmin = dR
          tmoth = tau
      if dRmin<0.4: # found mother tau
        if tmoth.vistau!=None: # visible decay product already set => ignore
          print(f"WARNING! Multiple matches between tau and visible decay product!"
                "{vistau} ({vistau.dm}) will be ignored in favor of {tmoth.vistau} ({tmoth.vistau.dm})!")
        else: # set visible decay product for first time
          tmoth.vistau = vistau # assign visible daughter to tau
          vistau.settau(tmoth) # set tau and mother
      hadtaus.append(vistau)
      vistaus.append(vistau)
      self.out.fill('dR_vt',dRmin) # DeltaR between visible tau and closest "full" tau lepton
    
    # AK4 JETS (gen-level)
    # All hadronic jets at gen-level, excluding hadronic tau decays
    ht = 0
    for jet in genjets:
      dRmin_tau = getdRmin(jet,taus)
      self.out.fill('dR_jt',getdRmin(jet,taus)) # DeltaR between jet and closest tau
      if abs(jet.partonFlavour)==15 or (abs(jet.partonFlavour)==0 and dRmin_tau<0.3):
        continue # remove overlap with taus
      jets.append(jet) # inclusive (except taus)
      if abs(jet.partonFlavour)==5: # b quark
        bjets.append(jet)
      if jet.pt>20:
        ht += sqrt( jet.mass*jet.mass + jet.pt*jet.pt )
        if abs(jet.eta)<2.5: # central jets (barrel)
          cjets.append(jet)
        elif abs(jet.eta)<4.7: # forward jets (endcaps, 2.5<|eta|<4.7)
          fjets.append(jet)
    
    # LQ DECAYS to TOP
    #if len(ntops)>=1:
    #  return False # do not store event if it contains a top quark
    if len(tops)==0:
      self.out.cutflow.fill('notop')
    
    # FILL BRANCHES
    self.out.genweight[0]    = event.genWeight
    self.out.nlqs[0]         = len(lqs)
    self.out.nbots[0]        = len(bots)
    self.out.nbots20[0]      = sum(b.pt>20 and abs(b.eta)<2.5 for b in bots)
    self.out.ntops[0]        = len(tops)
    self.out.nelecs[0]       = len(elecs)
    self.out.nmuons[0]       = len(muons)
    self.out.nleptaus[0]     = len(leptaus) # leptonic decay modes
    self.out.nleptaus20[0]   = sum(t.pt>20 and abs(t.eta)<2.5 for t in leptaus) # hadronic decay modes
    self.out.nhadtaus[0]     = len(hadtaus) # hadronic decay modes
    self.out.nhadtaus20[0]   = sum(t.pt>20 and abs(t.eta)<2.5 for t in hadtaus) # hadronic decay modes
    self.out.ntaus[0]        = len(taus)
    self.out.ntaus20[0]      = sum(t.pt>20 and abs(t.eta)<2.5 for t in taus)
    self.out.ntnus[0]        = len(tnus)
    self.out.nnus[0]         = len(nus)
    self.out.nvistaus[0]     = len(vistaus)
    self.out.nvistaus20[0]   = sum(t.pt>20 and abs(t.eta)<2.5 for t in vistaus)
    self.out.nvistaus50[0]   = sum(t.pt>50 and abs(t.eta)<2.5 for t in vistaus)
    self.out.njets[0]        = len(jets)
    self.out.nbjets[0]       = len(bjets)
    self.out.nbjets20[0]     = sum(j.pt>20 and abs(j.eta)<2.5 for j in bjets)
    self.out.nbjets50[0]     = sum(j.pt>50 and abs(j.eta)<2.5 for j in bjets)
    self.out.ncjets20[0]     = len(cjets)
    self.out.ncjets50[0]     = sum(j.pt>50 for j in cjets)
    self.out.nfjets20[0]     = len(fjets)
    self.out.nfjets50[0]     = sum(j.pt>50 for j in fjets)
    self.out.ht[0]           = ht # sum transverse energy
    self.out.met[0]          = event.GenMET_pt
    self.out.metphi[0]       = event.GenMET_phi
    
    # FILL LQ BRANCHES
    if len(lqs)>=2: # LQ pair production
      lqs.sort(key=lambda lq: lq.pt,reverse=True) # sort LQ by pT
      lqs[0].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      lqs[1].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = lqs[1].pt
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = lqs[1].decays[0] if len(lqs[1].decays)>=1 else -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = lqs[1].decays[1] if len(lqs[1].decays)>=2 else -1
      self.out.m_lq[0]     = lqs[0].p4().M() # get mass from TLorentzVector
    elif len(lqs)>=1: # single LQ production
      lqs[0].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = -1
      self.out.m_lq[0]     = lqs[0].p4().M() # get mass from TLorentzVector
    else: # nonres. production (LQ in the t-channel)
      self.out.pt_lq1[0]   = -1
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = -1
      self.out.dau2_lq2[0] = -1
      self.out.m_lq[0]     = -1
    
    # FILL TAU HISTOGRAMS to study tau decay
    self.out.fill('dptmiss_nu',(p4_nu.Pt()-event.GenMET_pt)/event.GenMET_pt)
    self.out.fill('dphimiss_nu',p4_nu.Phi()-event.GenMET_phi)
    for tau in taus:
      dm = tau.vistau.dm if tau.vistau else 0
      if dm==3: # hadronic tau decay
        self.out.fill('pt_tau_vs_vis_had',tau.pt,tau.vistau.pt)
      elif dm in [1,2]: # leptonic tau decay
        self.out.fill('pt_tau_vs_vis_lep',tau.pt,tau.vistau.pt)
      if tau.pt>20: # to remove bias caused by pT > 10 GeV cut on GenVisTau
        self.out.fill('tau_dm',min(dm,3))
        self.out.fill('tau_dm_all',dm)
        if dm==3: # hadronic tau decay
          self.out.fill('dptvis_had',(tau.vistau.pt-tau.pt)/tau.pt)
        elif dm in [1,2]: # leptonic tau decay
          self.out.fill('dptvis_lep',(tau.vistau.pt-tau.pt)/tau.pt)
    
    # FILL TAU BRANCHES
    if len(taus)>=2:
      taus.sort(key=lambda t: t.pt,reverse=True) # sort taus by pT
      if taus[0].pt>20 and taus[1].pt>20: # to remove bias caused by pT > 10 GeV on GenVisTau
        dm1 = taus[0].vistau.dm if taus[0].vistau else 0
        dm2 = taus[1].vistau.dm if taus[1].vistau else 0
        self.out.fill('tau_dm2D',dm1,dm2) # hname, binx, biny
      ditau_p4               = taus[0].p4() + taus[1].p4() # ditau system
      self.out.dR_tt[0]      = taus[0].DeltaR(taus[1])
      self.out.m_tt[0]       = ditau_p4.M()
      self.out.pt_tt[0]      = ditau_p4.Pt()
      if (taus[0].vistau!=None and taus[1].vistau!=None):
        ditau_p4vis          = taus[0].vistau.p4 + taus[1].vistau.p4 # visible ditau system
        self.out.dRvis_tt[0] = taus[0].vistau.p4.DeltaR(taus[1].vistau.p4)
        self.out.mvis_tt[0]  = ditau_p4vis.M()
        self.out.ptvis_tt[0] = ditau_p4vis.Pt()
      else:
        self.out.dRvis_tt[0] = -2
        self.out.mvis_tt[0]  = -2
        self.out.ptvis_tt[0] = -2
      self.out.pt_tau1[0]    = taus[0].pt
      self.out.pt_tau2[0]    = taus[1].pt
      self.out.ptvis_tau1[0] = taus[0].vistau.pt if taus[0].vistau!=None else -2 # total visible momentum
      self.out.ptvis_tau2[0] = taus[1].vistau.pt if taus[1].vistau!=None else -2 # total visible momentum
      self.out.eta_tau1[0]   = taus[0].eta
      self.out.eta_tau2[0]   = taus[1].eta
      self.out.moth_tau1[0]  = taus[0].mother
      self.out.moth_tau2[0]  = taus[1].mother
      self.out.dm_tau1[0]    = taus[0].vistau.dm if taus[0].vistau!=None else 0
      self.out.dm_tau2[0]    = taus[1].vistau.dm if taus[1].vistau!=None else 0
    elif len(taus)>=1:
      self.out.dR_tt[0]      = -1
      self.out.dRvis_tt[0]   = -1
      self.out.m_tt[0]       = -1
      self.out.mvis_tt[0]    = -1
      self.out.pt_tt[0]      = -1
      self.out.ptvis_tt[0]   = -1
      self.out.pt_tau1[0]    = taus[0].pt
      self.out.pt_tau2[0]    = -1
      self.out.ptvis_tau1[0] = taus[0].vistau.pt if taus[0].vistau!=None else -2 # total visible momentum
      self.out.ptvis_tau2[0] = -1
      self.out.eta_tau1[0]   = taus[0].eta
      self.out.eta_tau2[0]   = -9
      self.out.moth_tau1[0]  = taus[0].mother
      self.out.moth_tau2[0]  = -1
      self.out.dm_tau1[0]    = taus[0].vistau.dm if taus[0].vistau!=None else 0
      self.out.dm_tau2[0]    = -1
    else: # no taus found
      self.out.dR_tt[0]      = -1
      self.out.dRvis_tt[0]   = -1
      self.out.m_tt[0]       = -1
      self.out.mvis_tt[0]    = -1
      self.out.pt_tt[0]      = -1
      self.out.ptvis_tt[0]   = -1
      self.out.pt_tau1[0]    = -1
      self.out.pt_tau2[0]    = -1
      self.out.ptvis_tau1[0] = -1
      self.out.ptvis_tau2[0] = -1
      self.out.eta_tau1[0]   = -9
      self.out.eta_tau2[0]   = -9
      self.out.moth_tau1[0]  = -1
      self.out.moth_tau2[0]  = -1
      self.out.dm_vistau1[0] = -1
      self.out.dm_vistau2[0] = -1
    
    # FILL VISIBLE TAU BRANCHES
    if len(vistaus)>=2:
      vistaus.sort(key=lambda t: t.pt,reverse=True) # sort vis. taus by pT
      if vistaus[0].dm<3 or vistaus[1].dm<3: # fully or semileptonic
        vistaus = vistaus[:2] # only keep leading vis. taus
        vistaus.sort(key=lambda t: (t.dm,-t.pt)) # sort leading vis. tau first by dm, then pT
      self.out.dR_ttvis[0]       = vistaus[0].p4.DeltaR(vistaus[1].p4)
      self.out.pt_vistau1[0]     = vistaus[0].pt
      self.out.pt_vistau2[0]     = vistaus[1].pt
      self.out.eta_vistau1[0]    = vistaus[0].eta
      self.out.eta_vistau2[0]    = vistaus[1].eta
      self.out.phi_vistau1[0]    = vistaus[0].phi
      self.out.phi_vistau2[0]    = vistaus[1].phi
      self.out.moth_vistau1[0]   = vistaus[0].mother
      self.out.moth_vistau2[0]   = vistaus[1].mother
      self.out.dm_vistau1[0]     = vistaus[0].dm
      self.out.dm_vistau2[0]     = vistaus[1].dm
      self.out.mt_vistau1[0]     = vistaus[0].mt(event.GenMET_pt,event.GenMET_phi)
      self.out.mt_vistau2[0]     = vistaus[1].mt(event.GenMET_pt,event.GenMET_phi)
      self.out.dphi_vistau[0]    = vistaus[0].p4.DeltaPhi(vistaus[1].p4)
    elif len(vistaus)>=1:
      self.out.dR_ttvis[0]       = -1
      self.out.pt_vistau1[0]     = vistaus[0].pt
      self.out.pt_vistau2[0]     = -1
      self.out.eta_vistau1[0]    = vistaus[0].eta
      self.out.eta_vistau2[0]    = -9
      self.out.phi_vistau1[0]    = vistaus[0].phi
      self.out.phi_vistau2[0]    = -9
      self.out.moth_vistau1[0]   = vistaus[0].mother
      self.out.moth_vistau2[0]   = 0
      self.out.dm_vistau1[0]     = vistaus[0].dm
      self.out.dm_vistau2[0]     = -1
      self.out.mt_vistau1[0]     = vistaus[0].mt(event.GenMET_pt,event.GenMET_phi)
      self.out.mt_vistau2[0]     = -1
      self.out.dphi_vistau[0]    = -9
    else: # no visible taus found
      self.out.dR_ttvis[0]       = -1
      self.out.pt_vistau1[0]     = -1
      self.out.pt_vistau2[0]     = -1
      self.out.eta_vistau1[0]    = -9
      self.out.eta_vistau2[0]    = -9
      self.out.phi_vistau1[0]    = -9
      self.out.phi_vistau2[0]    = -9
      self.out.moth_vistau1[0]   = 0
      self.out.moth_vistau2[0]   = 0
      self.out.dm_vistau1[0]     = -1
      self.out.dm_vistau2[0]     = -1
      self.out.mt_vistau1[0]     = -1
      self.out.mt_vistau2[0]     = -1
      self.out.dphi_vistau[0]    = -9
    
    # FILL BOTTOM QUARK BRANCHES
    if len(bots)>=2:
      bots.sort(key=lambda t: t.pt,reverse=True) # sort bottom quarks by pT
      self.out.dR_bb[0]     = bots[0].DeltaR(bots[1])
      self.out.pt_bot1[0]   = bots[0].pt
      self.out.pt_bot2[0]   = bots[1].pt
      self.out.eta_bot1[0]  = bots[0].eta
      self.out.eta_bot2[0]  = bots[1].eta
      self.out.moth_bot1[0] = bots[0].mother
      self.out.moth_bot2[0] = bots[1].mother
    elif len(bots)>=1:
      self.out.dR_bb[0]     = -1
      self.out.pt_bot1[0]   = bots[0].pt
      self.out.pt_bot2[0]   = -1
      self.out.eta_bot1[0]  = bots[0].eta
      self.out.eta_bot2[0]  = -9
      self.out.moth_bot1[0] = bots[0].mother
      self.out.moth_bot2[0] = -1
    else: # no bots found
      self.out.dR_bb[0]     = -1
      self.out.pt_bot1[0]   = -1
      self.out.pt_bot2[0]   = -1
      self.out.eta_bot1[0]  = -9
      self.out.eta_bot2[0]  = -9
      self.out.moth_bot1[0] = -1
      self.out.moth_bot2[0] = -1
    
    # FILL JET BRANCHES
    if len(jets)>=2:
      jets.sort(key=lambda j: j.pt,reverse=True) # sort jets by pT
      self.out.pt_jet1[0]     = jets[0].pt
      self.out.pt_jet2[0]     = jets[1].pt
      self.out.eta_jet1[0]    = jets[0].eta
      self.out.eta_jet2[0]    = jets[1].eta
      self.out.flavor_jet1[0] = jets[0].partonFlavour
      self.out.flavor_jet2[0] = jets[1].partonFlavour
    elif len(jets)>=1:
      self.out.pt_jet1[0]     = jets[0].pt
      self.out.pt_jet2[0]     = -1
      self.out.eta_jet1[0]    = jets[0].eta
      self.out.eta_jet2[0]    = -9
      self.out.flavor_jet1[0] = jets[0].partonFlavour
      self.out.flavor_jet2[0] = 0
    else: # no jets found
      self.out.pt_jet1[0]     = -1
      self.out.pt_jet2[0]     = -1
      self.out.eta_jet1[0]    = -9
      self.out.eta_jet2[0]    = -9
      self.out.flavor_jet1[0] = 0
      self.out.flavor_jet2[0] = 0
    
    # FILL B JET BRANCHES
    if len(bjets)>=2:
      bjets.sort(key=lambda j: j.pt,reverse=True) # sort b jets by pT
      self.out.pt_bjet1[0]  = bjets[0].pt
      self.out.pt_bjet2[0]  = bjets[1].pt
      self.out.eta_bjet1[0] = bjets[0].eta
      self.out.eta_bjet2[0] = bjets[1].eta
    elif len(bjets)>=1:
      self.out.pt_bjet1[0]  = bjets[0].pt
      self.out.pt_bjet2[0]  = -1
      self.out.eta_bjet1[0] = bjets[0].eta
      self.out.eta_bjet2[0] = -9
    else: # no b jets found
      self.out.pt_bjet1[0]  = -1
      self.out.pt_bjet2[0]  = -1
      self.out.eta_bjet1[0] = -9
      self.out.eta_bjet2[0] = -9
    
    # FILL HISTOGRAMS
    for lq in lqs:
      mass = lq.p4().M() # get mass from TLorentzVector
      self.out.fill('mass_lq',mass)
    
    self.out.fill() # fill branches
    return True
  

# QUICK PLOTTING SCRIPT
if __name__ == '__main__':
  
  # USER OPTIONS
  from argparse import ArgumentParser
  parser = ArgumentParser()
  parser.add_argument('-i',   '--infiles', nargs='+')
  parser.add_argument('-o',   '--outdir', default='.')
  parser.add_argument('-tag', '--tag', default='', help="extra tag for name of output file")
  parser.add_argument('-n',   '--maxevts', type=int, default=10000)
  parser.add_argument('-L',   '--lq', choices=['s','p','t','x'], default='t',
                                      help="select pre-defined list of input files for pair ('p'), single ('s'), or nonres. ('t')")
  args = parser.parse_args()
  
  # SETTINGS
  maxevts   = args.maxevts if args.maxevts>0 else None
  outfname  = "genAnalyzer_LQ%s.root"%(args.tag)
  modules   = [ModuleGenLQ(outfname)]
  #branchsel = "keep_and_drop_gen.txt" # only keep gen-related branches to speed up processing
  
  # INPUT FILES
  url = "root://cms-xrd-global.cern.ch/"
  indir = "/eos/user/i/ineuteli/public/forCalTech/NANOAOD/"
  if args.infiles:
    infiles = args.infiles
  elif args.lq=='p': # LQ pair production
    # for d in /eos/user/i/ineuteli/public/forCalTech/NANOAOD/*1400*/*/*; do ls $d/*root | head; done
    infiles = [
      indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_100_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_101_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_102_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_103_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_104_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_106_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_107_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_108_skimmed_JECSys.root",
    ]
  elif args.lq=='s': # single LQ production
    infiles = [
      indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_100_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_101_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_102_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_103_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_104_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_105_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_106_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_107_skimmed_JECSys.root",
    ]
  elif args.lq=='t': # nonresonant production
    infiles = [
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_0_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_10_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_11_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_12_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_100_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_101_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_102_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_103_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_104_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_105_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_106_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_107_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_108_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_109_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_110_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_111_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_112_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_113_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_114_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_115_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_116_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_117_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_118_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_119_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_120_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_121_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_122_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_123_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_124_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_125_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_126_skimmed_JECSys.root",
    ]
  else:
    infiles = [
      #url+'/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/280000/525CD279-3344-6043-98B9-2EA8A96623E4.root',
      url+'/store/mc/RunIISummer20UL18NanoAODv9/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/130000/44187D37-0301-3942-A6F7-C723E9F4813D.root',
    ]
  
  # PROCESS NANOAOD
  processor = PostProcessor(args.outdir,infiles,modules=modules,maxEntries=maxevts,
                            branchsel=branchsel,noOut=True)
  processor.run()
  
