#! /usr/bin/env python
# Author: Izaak Neutelings (May 2022)
# Description: Study gen filter of mutau events for stitching of DYJetsToLL_M-50
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/MCStitching
# Instructions:
#   pico.py channel genmutau GenFilterMuTau
#   pico.py run -c genmutau -y UL2018 -s DYJetsToLL_M-50 DYJetsToMuTauh -m 10000
#   python/analysis/GenFilterMuTau.py DYJetsToLL=output/pico_genmutau_UL2018_DYJetsToLL_M-50.root DYJetsToMuTauh=output/pico_genmutau_UL2018_DYJetsToMuTauh_M-50.root
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import re
from ROOT import TLorentzVector, TH1D, TH2D, gStyle, kRed
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.PicoProducer.analysis.utils import hasbit, filtermutau, statusflags_dict, dumpgenpart, getdecaychain, getmother, deltaPhi

#isHardProcTau = lambda p: p.statusflag('isHardProcessTauDecayProduct') or p.statusflag('isDirectHardProcessTauDecayProduct')
countHardProcTau = lambda l: sum(1 for p in l if p.statusflag('isHardProcessTauDecayProduct') or p.statusflag('isDirectHardProcessTauDecayProduct'))


class GenFilterMuTau(Module):
  """Simple module to study decays and gen filters in DY samples."""
  
  def __init__(self,fname,**kwargs):
    self.out = TreeProducerGenFilterMuTau(fname,self)
    self.verb = kwargs.get('verb',0)
    print(">>> verb = %r"%(self.verb))
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('none')
    self.out.h_nup.Fill(event.LHE_Njets)
    #self.out.h_weight.Fill(event.LHE_Njets)
    
    # SELECT PROMPT CANDIDATES
    elecs        = [ ] # all (unique) elecs
    muons        = [ ] # all (unique) muons
    taus         = [ ] # all (unique) taus
    elecs_hard   = [ ] # from hard process electrons
    muons_hard   = [ ] # from hard process muons
    taus_hard    = [ ] # from hard process taus
    taus_unst    = [ ] # from hard process taus for FSR photon check
    taus_brem    = [ ] # from hard process taus that radiate FSR photon
    elecs_tau    = [ ] # electrons from decay of prompt tau
    muons_tau    = [ ] # muons from decay of prompt tau
    tauhs_hard   = [ ] # hadronic tau from prompt tau decay
    particles = Collection(event,'GenPart')
    for particle in particles:
      pid = abs(particle.pdgId)
      ###self.out.fillStatusFlag(particle) # check correlations
      if pid==15 and particle.status!=2 and particle.statusflag('fromHardProcess'): # probably status==23
        taus_unst.append(particle) # for FSR photon check
      if pid<16 and particle.statusflag('isLastCopy'): # ignore duplicate particles before FSR
        # https://github.com/cms-sw/cmssw/blob/e48b3c4c1c95b0bb8baa89b216313f012877a73e/PhysicsTools/NanoAOD/python/genparticles_cff.py#L8-L28
        if pid==11:
          elecs.append(particle)
          if particle.statusflag('isDirectTauDecayProduct'): # use "direct" to remove tau -> pi0 -> e+e-
            elecs_tau.append(particle)
          elif particle.statusflag('fromHardProcess'):
            elecs_hard.append(particle)
        elif pid==13: #particle.status==2:
          muons.append(particle)
          if particle.statusflag('isDirectTauDecayProduct'):
            muons_tau.append(particle)
          elif particle.statusflag('fromHardProcess'):
            muons_hard.append(particle)
        elif pid==15:
          if particle.status==2:
            particle.pvis = TLorentzVector() # build visible four-momentum for hadronic decays
            taus.append(particle) # all tau
            if particle.statusflag('fromHardProcess'):
              taus_hard.append(particle) # taus from hard process
            #else:
            #  taus_hard.append(particle)
      elif pid>16: # ignore neutrinos and charged leptons
        if pid==22: # photon
          for tau in taus_unst: # find actual radiating tau
            if tau._index==particle.genPartIdxMother:
              taus_brem.append(tau)
              break
        for tau in taus:
          if tau._index==particle.genPartIdxMother: # non-leptonic tau decay product
            #print(">>> add %+d to %+d"%(particle.pdgId,tau.pdgId))
            tau.pvis += particle.p4() # add visible tau decay product
            if tau not in tauhs_hard:
              tauhs_hard.append(tau)
    
    #### HADRONIC TAUS
    ###if len(taus_hard)>=1:
    ###  #print '-'*20+" 2 taus "
    ###  genvistaus = Collection(event,'GenVisTau') # slimmed with pt > 10 # not complete
    ###  for tau in taus_hard:
    ###    dRmin = 3.0
    ###    match = None
    ###    for genvistau in genvistaus:
    ###      dR = tau.DeltaR(genvistau)
    ###      if dR<dRmin and tau.pdgId*genvistau.charge<0: # same charge
    ###        dRmin = dR
    ###        match = genvistau
    ###    if match:
    ###      self.out.h_dR_tauh.Fill(dRmin)
    ###      if dRmin<0.5: # and genvistau in tauhs_hard
    ###        tauhs_hard.append(match)
    
    #### CHECK FOR OVERLAPPING ELECTRONS
    ###if elecs_tau or muons_tau:
    ###  print '-'*80
    ###  for particle in elecs_tau+muons_tau:
    ###    dumpgenpart(particle,particles,grand=True,flags=['isPrompt','fromHardProcess','isDirectTauDecayProduct',
    ###      'isHardProcessTauDecayProduct','isDirectHardProcessTauDecayProduct']) #,'isLastCopyBeforeFSR','isLastCopy'])
    ###for i, elec1 in enumerate(elecs):
    ###  for elec2 in elecs[i+1:]:
    ###    self.out.h_dR_elec.Fill(elec1.DeltaR(elec2))
    
    # TAU RADIATING FSR PHOTON
    # Checking taus radiating FSR photons for bug in EmbeddingHepMCFilter
    # pre-CMSSW_10_6_30_patch1 affecting Summer19 and Summer20 UL
    # Buggy Pythia8 filter:
    #   https://indico.cern.ch/event/1170879/#2-validation-of-exclusive-dy-t
    #   https://github.com/cms-sw/cmssw/pull/38829
    taus_brem_final = [ ] # final taus from hard process that have radiated earlier
    muons_tau_brem  = [ ] # muons from radiating taus from hard process
    for tau in taus_hard: # loop over final taus from hard process
      moth = tau
      while abs(moth.pdgId)==15 and moth.genPartIdxMother>=0: # go back up tau chain
        if any(t._index==moth.genPartIdxMother for t in taus_brem): # match with radiating tau
          taus_brem_final.append(moth) # save for checking decay
          self.out.h_qtau_brem.Fill(-tau.pdgId/15) # charge
          break
        moth = particles[moth.genPartIdxMother] # check tau mother if tau again
    for muon in muons_tau: # loop over muons from tau decay
      moth = muon
      charge = -muon.pdgId/13
      self.out.h_qmuon_tau.Fill(charge)
      while abs(moth.pdgId)==13 and moth.genPartIdxMother>=0: # go back up muon chain
        if any(t._index==moth.genPartIdxMother for t in taus_brem_final): # match with radiating tau
          muons_tau_brem.append(muon)
          self.out.h_qmuon_tau_brem.Fill(charge) # charge
          break
        moth = particles[moth.genPartIdxMother] # check muon mother if tau again
    self.out.h_nmuon_tau_brem.Fill(len(muons_tau_brem)) # count number of muons from radiating tau
    
    # FILL HISTOGRAMS
    self.out.h_nelec.Fill(len(elecs))
    self.out.h_nelec_tau.Fill(len(elecs_tau))
    self.out.h_nelec_hard.Fill(len(elecs_hard))
    self.out.h_nmuon.Fill(len(muons))
    self.out.h_nmuon_tau.Fill(len(muons_tau))
    self.out.h_nmuon_hard.Fill(len(muons_hard))
    self.out.h_ntau.Fill(len(taus))
    self.out.h_ntau_hard.Fill(len(taus_hard))
    self.out.h_ntau_brem.Fill(len(taus_brem)) # radiating FSR photon
    self.out.h_ntauh_hard.Fill(len(tauhs_hard))
    self.out.h_nmuon_nelec.Fill(len(muons_hard),len(elecs_hard))
    self.out.h_nmuon_nelec_tau.Fill(len(muons_tau),len(elecs_tau))
    self.out.h_ntau_nelec.Fill(len(taus_hard),len(elecs_hard))
    self.out.h_ntau_nelec_tau.Fill(len(taus_hard),len(elecs_tau))
    self.out.h_ntauh_nelec_tau.Fill(len(tauhs_hard),len(elecs_tau))
    self.out.h_ntau_nmuon.Fill(len(taus_hard),len(muons_hard))
    self.out.h_ntau_nmuon_tau.Fill(len(taus_hard),len(muons_tau))
    self.out.h_ntauh_nmuon.Fill(len(tauhs_hard),len(muons_hard))
    self.out.h_ntauh_nmuon_tau.Fill(len(tauhs_hard),len(muons_tau))
    self.out.h_ntau_ntauh.Fill(len(taus_hard),len(tauhs_hard))
    
    # CUTFLOW Z/gamma -> ll
    if len(elecs_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('ee')
    if len(muons_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('mumu')
    if len(taus_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('tautau')
    elif len(elecs_hard)<2 and len(muons_hard)<2:
      self.out.cutflow.fill('unknown')
    
    # TAU DECAYS
    ntauhs = len(tauhs_hard) #event.nGenVisTau
    taus_hard_pt18 = sum(1 for p in taus_hard if p.pt>18)>=2 # GenVisTau, has pt>10
    #if len(taus_hard)>=2:
    if len(elecs_tau)>=1 and ntauhs>=1:
      self.out.cutflow.fill('etauh')
      if taus_hard_pt18 and countHardProcTau(elecs_tau)>=1:
        self.out.cutflow.fill('etauh_hard')
    if len(muons_tau)>=1 and ntauhs>=1:
      self.out.cutflow.fill('mutauh')
      if taus_hard_pt18 and countHardProcTau(muons_tau)>=1:
        self.out.cutflow.fill('mutauh_hard')
    if ntauhs>=2:
      self.out.cutflow.fill('tauhtauh')
      if taus_hard_pt18:
        self.out.cutflow.fill('tauhtauh_hard')
    if len(elecs_tau)+len(muons_tau)>=2:
      self.out.cutflow.fill('taultaul')
      if taus_hard_pt18 and countHardProcTau(elecs_tau)+countHardProcTau(muons_tau)>=2:
        self.out.cutflow.fill('taultaul_hard')
    
    # CHECK FOR MISSING DECAYS
    if self.verb>=2 and len(taus_hard)>=2 and len(elecs_tau)+len(muons_tau)+ntauhs<2:
      print(">>> MISSING DITAU DECAY? electrons=%d (%d), muons=%d (%d), tauh=%d"%(
        len(elecs_tau),len(elecs),len(muons_tau),len(muons),ntauhs))
      for tau in taus_hard:
        print(getdecaychain(tau,particles))
      for particle in particles:
        pid = abs(particle.pdgId)
        if pid in [11,13,15,16]:
          dumpgenpart(particle,particles,grand=True,flags=['fromHardProcess',
            'isDirectTauDecayProduct','isHardProcessTauDecayProduct','isDirectHardProcessTauDecayProduct','isLastCopy'])
    
    # MUTAU FILTER
    mutaufilter = filtermutau(event)
    self.out.h_mutaufilter.Fill(mutaufilter)
    
    # SELECT MUTAU EVENTS FOR BRANCHES
    if len(muons)==0 or len(tauhs_hard)==0:
      return False
    
    # MOTHER PDG ID
    moth_pid = abs(getmother(taus_hard[0],particles).pdgId) if len(taus_hard)>=1 else 0
    if len(taus_hard)>=2:
      moth_pid2 = abs(getmother(taus_hard[1],particles).pdgId)
      if moth_pid!=moth_pid2:
        print(">>> Mother of ditau does not match! %s vs %s"%(moth_pid,moth_pid2))
    self.out.h_mothpid.Fill(moth_pid)
    
    # FILL TREE BRANCHES
    muon = max(muons,key=lambda m: m.pt)
    tauh = max(tauhs_hard,key=lambda t: t.pvis.Pt())
    if len(taus_hard)>=2:
      taus_hard = sorted(taus_hard,key=lambda t: -t.pt)
      self.out.pt_1[0]       = taus_hard[0].pt
      self.out.pt_2[0]       = taus_hard[1].pt
      self.out.eta_1[0]      = taus_hard[0].eta
      self.out.eta_2[0]      = taus_hard[1].eta
      self.out.dR[0]         = taus_hard[0].DeltaR(taus_hard[1])
      self.out.deta[0]       = abs(taus_hard[0].eta-taus_hard[1].eta)
      self.out.dphi[0]       = deltaPhi(taus_hard[0].phi,taus_hard[1].phi)
    elif len(taus_hard)>=1:
      self.out.pt_1[0]       = taus_hard[0].pt
      self.out.pt_2[0]       = -1
      self.out.eta_1[0]      = taus_hard[0].eta
      self.out.eta_2[0]      = -9
      self.out.dR[0]         = -1
      self.out.deta[0]       = -1
      self.out.dphi[0]       = -1
    else: # defaults
      self.out.pt_1[0]       = -1
      self.out.pt_2[0]       = -1
      self.out.eta_1[0]      = -9
      self.out.eta_2[0]      = -9
      self.out.dR[0]         = -1
      self.out.deta[0]       = -1
      self.out.dphi[0]       = -1
    self.out.mu_pt[0]        = muon.pt
    self.out.mu_eta[0]       = muon.eta
    self.out.mu_q[0]         = -muon.pdgId/13
    self.out.mu_fromTau[0]   = muon.statusflag('isDirectTauDecayProduct')
    self.out.mu_fromHard[0]  = muon.statusflag('fromHardProcess') or muon.statusflag('isHardProcessTauDecayProduct') or muon.statusflag('isDirectHardProcessTauDecayProduct')
    if len(muons_tau)>=1:
      muon_tau = max(muons_tau,key=lambda m: m.pt)
      self.out.mu_tau_pt[0]       = muon_tau.pt
      self.out.mu_tau_eta[0]      = muon_tau.eta
      self.out.mu_tau_q[0]        = -muon_tau.pdgId/13
      self.out.mu_tau_fromHard[0] = muon_tau.statusflag('fromHardProcess') or muon.statusflag('isHardProcessTauDecayProduct') or muon.statusflag('isDirectHardProcessTauDecayProduct')
    else: # defaults
      self.out.mu_tau_pt[0]       = -1
      self.out.mu_tau_eta[0]      = -9
      self.out.mu_tau_q[0]        = -9
      self.out.mu_tau_fromHard[0] = False
    self.out.moth_pid[0]     = moth_pid
    self.out.tauh_pt[0]      = tauh.pt
    self.out.tauh_eta[0]     = tauh.eta
    self.out.tauh_q[0]       = -tauh.pdgId/15
    self.out.nelecs[0]       = len(elecs)
    self.out.nelecs_tau[0]   = len(elecs_tau)
    self.out.nelecs_hard[0]  = len(elecs_hard)
    self.out.nmuons[0]       = len(muons)
    self.out.nmuons_tau[0]   = len(muons_tau)
    self.out.nmuons_hard[0]  = len(muons_hard)
    self.out.ntaus[0]        = len(taus)
    self.out.ntaus_hard[0]   = len(taus_hard)
    self.out.ntauhs_hard[0]  = len(tauhs_hard)
    self.out.mutaufilter[0]  = mutaufilter
    self.out.fill()
    
    return True
    

class TreeProducerGenFilterMuTau(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerGenFilterMuTau,self).__init__(filename,module,**kwargs)
    
    # CUTFLOW
    self.cutflow.addcut('none',         "no cut"       )
    self.cutflow.addcut('ll',           "ll"           )
    self.cutflow.addcut('ee',           "ee"           )
    self.cutflow.addcut('mumu',         "mumu"         )
    self.cutflow.addcut('tautau',       "tautau"       )
    self.cutflow.addcut('unknown',      "unknown"      )
    self.cutflow.addcut('etauh',        "etauh"        )
    self.cutflow.addcut('mutauh',       "mutauh"       )
    self.cutflow.addcut('tauhtauh',     "tauhtauh"     )
    self.cutflow.addcut('taultaul',     "taultaul"     )
    self.cutflow.addcut('etauh_hard',   "etauh_hard"   )
    self.cutflow.addcut('mutauh_hard',  "mutauh_hard"  )
    self.cutflow.addcut('tauhtauh_hard',"tauhtauh_hard")
    self.cutflow.addcut('taultaul_hard',"taultaul_hard")
    
    # 1D HISTOGRAMS
    self.h_nup             = TH1D('h_nup',           ";Number of partons at LHE level;Events",9,0,9)
    self.h_mothpid         = TH1D('h_mothpid',       ";Mother PID ;#tau#tau events",40,0,40)
    self.h_dR_tauh         = TH1D('h_dR_tauh',       ";#DeltaR(#tau,#tau_{#lower[-0.2]{h}});Tau leptons",50,0,4)
    ###self.h_dR_elec         = TH1D('h_dR_elec',      ";#DeltaR(e,e);Electron pairs",50,0,4)
    self.h_mutaufilter     = TH1D('h_mutaufilter',   ";mutaufilter (pt>18, |eta|<2.5);Events",5,0,5)
    self.h_nelec           = TH1D('h_nelec',         ";Number of generator electrons;Events",8,0,8)
    self.h_nelec_tau       = TH1D('h_nelec_tau',     ";Number of electrons from #tau decay;Events",8,0,8)
    self.h_nelec_hard      = TH1D('h_nelec_hard',    ";Number of electrons from hard process;Events",8,0,8)
    self.h_nmuon           = TH1D('h_nmuon',         ";Number of generator muons;Events",8,0,8)
    self.h_nmuon_tau       = TH1D('h_nmuon_tau',     ";Number of muons from tau decay;Events",8,0,8)
    self.h_nmuon_hard      = TH1D('h_nmuon_hard',    ";Number of muons from hard process;Events",8,0,8)
    self.h_nmuon_tau_brem  = TH1D('h_nmuon_tau_brem',";Number of muons from radiating #tau;Events",8,0,8)
    self.h_ntau            = TH1D('h_ntau',          ";Number of generator #tau leptons;Events",8,0,8)
    self.h_ntau_hard       = TH1D('h_ntau_hard',     ";Number of #tau leptons from hard process;Events",8,0,8)
    self.h_ntau_brem       = TH1D('h_ntau_brem',     ";Number of radiating #tau leptons from hard process;Events",8,0,8)
    self.h_ntauh_hard      = TH1D('h_ntauh_hard',    ";Number of #tau_{#lower[-0.2]{h}} leptons;Events",8,0,8)
    self.h_qtau_brem       = TH1D('h_qtau_brem',     ";Charge of radiating #tau;Events",6,-2,4)
    self.h_qmuon_tau       = TH1D('h_qmuon_tau',     ";Charge of muons from #tau decay;Events",6,-2,4)
    self.h_qmuon_tau_brem  = TH1D('h_qmuon_tau_brem',";Charge of muons from radiating #tau;Events",6,-2,4)
    
    # 2D HISTOGRAMS
    self.h_nmuon_nelec     = TH2D('h_nmuon_nelec',    ";Number of muons from hard process;Number of electrons from hard process",8,0,8,8,0,8)
    self.h_nmuon_nelec_tau = TH2D('h_nmuon_nelec_tau',";Number of muons from #tau decay;Number of electrons from #tau decay",8,0,8,8,0,8)
    self.h_ntau_nelec      = TH2D('h_ntau_nelec',     ";Number of taus from hard process;Number of electrons from hard process",8,0,8,8,0,8)
    self.h_ntau_nelec_tau  = TH2D('h_ntau_nelec_tau', ";Number of taus from hard process;Number of electrons from #tau decay",8,0,8,8,0,8)
    self.h_ntauh_nelec_tau = TH2D('h_ntauh_nelec_tau',";Number of #tau_{#lower[-0.2]{h}} from hard process;Number of electrons from #tau decay",8,0,8,8,0,8)
    self.h_ntau_nmuon      = TH2D('h_ntau_nmuon',     ";Number of taus from hard process;Number of muons from hard process",8,0,8,8,0,8)
    self.h_ntau_nmuon_tau  = TH2D('h_ntau_nmuon_tau', ";Number of taus from hard process;Number of muons from #tau decay",8,0,8,8,0,8)
    self.h_ntauh_nmuon     = TH2D('h_ntauh_nmuon',    ";Number of #tau_{#lower[-0.2]{h}} from hard process;Number of muons from hard process",8,0,8,8,0,8)
    self.h_ntauh_nmuon_tau = TH2D('h_ntauh_nmuon_tau',";Number of #tau_{#lower[-0.2]{h}} from hard process;Number of muons from #tau decay",8,0,8,8,0,8)
    self.h_ntau_ntauh      = TH2D('h_ntau_ntauh',     ";Number of taus from hard process;Number of #tau_{#lower[-0.2]{h}} from hard process",8,0,8,8,0,8)
    ###self.h_statusflags     = TH2D('h_statusflags',    ";Status flags;Status flags;Gen particles",15,0,15,15,0,15)
    for hist in [self.h_nmuon_nelec,self.h_nmuon_nelec_tau,self.h_ntauh_nmuon_tau,self.h_ntauh_nelec_tau,
                 self.h_ntau_nelec,self.h_ntau_nelec_tau,self.h_ntau_ntauh,
                 self.h_ntau_nmuon,self.h_ntau_nmuon_tau,self.h_ntauh_nmuon]:
      hist.SetOption('COLZ')
    
    # TREE BRANCHES
    self.addBranch('pt_1',            'f', title="Leading tau lepton (from hard process) pT")
    self.addBranch('eta_1',           'f', title="Leading tau lepton (from hard process) eta")
    self.addBranch('pt_2',            'f', title="Subleading tau lepton (from hard process) pT")
    self.addBranch('eta_2',           'f', title="Subleading tau lepton (from hard process) eta")
    self.addBranch('dR',              'f', title="DeltaR between tau leptons (from hard process)")
    self.addBranch('deta',            'f', title="Deltaeta between tau leptons (from hard process)")
    self.addBranch('dphi',            'f', title="Deltaphi between tau leptons (from hard process)")
    self.addBranch('mu_pt',           'f', title="Muon pT")
    self.addBranch('mu_eta',          'f', title="Muon eta")
    self.addBranch('mu_q',            'i', title="Muon charge")
    self.addBranch('mu_fromTau',      '?', title="Muon isDirectTauDecayProduct")
    self.addBranch('mu_fromHard',     '?', title="Muon fromHardProcess")
    self.addBranch('mu_tau_pt',       'f', title="Muon (from tau decay) pT")
    self.addBranch('mu_tau_eta',      'f', title="Muon (from tau decay) eta")
    self.addBranch('mu_tau_q',        'f', title="Muon (from tau decay) charge")
    self.addBranch('mu_tau_fromHard', '?', title="Muon (from tau decay) fromHardProcess")
    self.addBranch('moth_pid',        'i', title="PDG ID")
    self.addBranch('tauh_pt',         'f', title="Visible tauh pT")
    self.addBranch('tauh_eta',        'f', title="Visible tauh eta")
    self.addBranch('tauh_q',          'i', title="Visible tauh charge")
    self.addBranch('nelecs',          'i', title="Number of gen electrons")
    self.addBranch('nelecs_tau',      'i', title="Number of gen electrons from tau decays")
    self.addBranch('nelecs_hard',     'i', title="Number of gen electrons from hard process")
    self.addBranch('nmuons',          'i', title="Number of gen muons")
    self.addBranch('nmuons_tau',      'i', title="Number of gen muons from tau decays")
    self.addBranch('nmuons_hard',     'i', title="Number of gen muons from hard process")
    self.addBranch('ntaus',           'i', title="Number of gen taus")
    self.addBranch('ntaus_hard',      'i', title="Number of gen taus from hard process")
    self.addBranch('ntauhs_hard',     'i', title="Number of gen tauhs from hard process")
    self.addBranch('mutaufilter',     '?', title="mutau filter")
    
  def endJob(self):
    """Write and close files after the job ends."""
    self.outfile.cd()
    
    # DITAU DECAYS
    ntau = self.cutflow.getbincontent('tautau')
    bins = [('etauh',23),('mutauh',23),('tauhtauh',42),('taultaul',12)]
    if ntau>0:
      for tag, title in [('',''),('_hard',' from hard process with tau pT > 18 GeV')]:
        ntau_decay = sum(self.cutflow.getbincontent(b+tag) for b, e in bins)
        print(">>> Ditau decays%s:"%(title))
        for bin, exp in bins:
          nbin = self.cutflow.getbincontent(bin+tag)
          print(">>> %8d / %5d = %5.2f%%   %6d / %d = %5.2f%%   %s, expect %s%%"%(
            nbin,ntau,100.0*nbin/ntau,nbin,ntau_decay,100.0*nbin/ntau_decay,bin,exp))
        print(">>> %8d / %5d = %5.2f%%   found ditau decays / all tau pairs"%(ntau_decay,ntau,100.0*ntau_decay/ntau))
    else:
      print(">>> No ditau...")
    
    # MUTAU FILTERS
    getfiltereff(self.h_mutaufilter)
    
    #### NORMALIZE STATUS FLAG CORRELATION MATRIX
    ###hist  = self.h_statusflags
    ###nxbins = hist.GetXaxis().GetNbins()
    ###nybins = hist.GetXaxis().GetNbins()
    ###hist.GetXaxis().SetLabelSize(0.038)
    ###hist.GetYaxis().SetLabelSize(0.038)
    ###hist.SetMarkerSize(1.4) # draw with "COLZ TEXT"
    ###hist.SetTitle("Normalized columns")
    ###hist.SetOption('COLZ TEXT') # preset default draw option
    ###gStyle.SetPaintTextFormat(".0f")
    ###for ix in range(1,nxbins+1): # loop over columns
    ###  ntot = hist.GetBinContent(ix,ix)
    ###  key  = [k for k, v in statusflags_dict.items() if v==ix-1][0]
    ###  hist.GetXaxis().SetBinLabel(ix,key)
    ###  hist.GetYaxis().SetBinLabel(ix,key)
    ###  for iy in range(1,nybins+1): # normalize rows
    ###    frac = 100.0*hist.GetBinContent(ix,iy)/ntot # fraction of column
    ###    hist.SetBinContent(ix,iy,frac) # overwrite number of entries with fraction
    ###gStyle.Write('style')
    
    super(TreeProducerGenFilterMuTau,self).endJob()
  
  def fillStatusFlag(self,particle):
    for xbit in range(0,15):
      if not hasbit(particle.statusFlags,xbit): continue
      for ybit in range(0,15):
        if not hasbit(particle.statusFlags,ybit): continue
        self.h_statusflags.Fill(xbit,ybit)
  

def getfiltereff(hist):
  eff   = -1
  npass = hist.GetBinContent(2)
  ntot  = hist.GetBinContent(1)+npass
  assert ntot==hist.Integral(), "Bins do not add up!?"
  if ntot>0:
    # https://cms-pdmv.cern.ch/mcm/edit?db_name=requests&prepid=TAU-RunIISummer19UL18wmLHEGEN-00007&page=0
    eff = npass/ntot
    print(">>> Efficiency of custom mutau gen-filter (pT>18, |eta|<2.5):")
    print(">>> %8d / %5d = %5.3f%%"%(npass,ntot,100.0*npass/ntot))
    print(">>> Expect ~ 0.888 % = B(ll->tautau) * eff(Z -> mutau) for DYJetsToLL_M-50 (pT>16, muon |eta|<2.5, tau |eta|<2.7)") # = 1.815e+03 / 5343.0 * 0.02615
    print(">>> Expect ~ 0.519 % = B(ll->tautau) * eff(Z -> mutau) for DYJetsToLL_M-50 (pT>18, |eta|<2.5, no FSR)") # = 1.815e+03 / 5343.0 * 0.02615 * 0.5841
  return eff
  

# QUICK PLOTTING SCRIPT
if __name__ == '__main__':
  from ROOT import gROOT, TFile
  from TauFW.Plotter.plot.Plot import Plot
  from argparse import ArgumentParser
  gROOT.SetBatch(True)      # don't open GUI windows
  gStyle.SetOptTitle(False) # don't make title on top of histogram
  gStyle.SetOptStat(False)  # don't make stat. box
  description = """Make histograms from output file."""
  parser = ArgumentParser(prog="GenMatcher",description=description,epilog="Good luck!")
  parser.add_argument('files', nargs='+', help="final (hadd'ed) ROOT file")
  parser.add_argument('-t',"--tag", default="", help="extra tag for output file")
  args = parser.parse_args()
  
  # OPEN FILES
  trees = [ ]
  for fname in args.files:
    if fname.count('=')==1:
      title, fname = fname.split('=')
    else:
      title = fname.replace('.root','')
    print(">>> Opening %s (%s)"%(fname,title))
    file = TFile.Open(fname,'READ')
    tree = file.Get('tree')
    tree.title = title
    tree.file = file
    trees.append(tree)
    
    # CHECK MUTAU FILTER EFFICIENCY
    hist = file.Get('h_mutaufilter')
    getfiltereff(hist)
    
  
  # DRAW NEW HISTOGRAMS
  selections = [
    #("nocuts",""),
    #("mutauh","ntaus_hard==2 && nmuons_tau>=1 && ntauhs_hard>=1"),
    ("mutauh from hard process","ntaus_hard==2 && nmuons_tau>=1 && ntauhs_hard>=1 && mu_tau_fromHard"),
    #("mutaufilter","mutaufilter"),
  ]
  vars = [
    ('pt_1',       50, 0,100),
    ('pt_2',       50, 0,100),
    ('eta_1',      35,-3,  4),
    ('eta_2',      35,-3,  4),
    ('mu_pt',      50, 0,100),
    ('mu_eta',     35,-3,  4),
    ('mu_q',        6,-2,  4),
    ('mu_tau_pt',  50, 0,100),
    ('mu_tau_eta', 35,-3,  4),
    ('mu_tau_q',    6,-2,  4),
    ('tauh_pt',    50, 0,100),
    ('tauh_eta',   35,-3,  4),
    ('tauh_q',      6,-2,  4),
    ('ntauhs_hard', 5, 0,  5),
    ('ntaus_hard',  5, 0,  5),
    ('dR',         40, 0,  4),
    ('dphi',       40, 0,  4),
    ('deta',       40, 0,  4),
  ]
  for stitle, sstring in selections:
    sname = stitle.replace(' ','').replace(',','-').replace('>','gt').replace('#','').replace('GeV','').replace('fromhardprocess','_hard')
    print(">>> Drawing %r..."%(stitle)) #,sstring)
    for xvar, nbins, xmin, xmax in vars:
      xtitle = trees[0].GetBranch(xvar).GetTitle() #xvar
      pname  = "%s_%s%s"%(xvar,sname,args.tag)
      hists  = [ ]
      for i, tree in enumerate(trees):
        hname  = "h_%s_%d"%(pname,i)
        title  = "%s;%s;Events"%(tree.title,xtitle)
        dcmd   = "%s >> %s"%(xvar,hname)
        hist   = TH1D(hname,title,nbins,xmin,xmax)
        out    = tree.Draw(dcmd,sstring,'gOff')
        print(">>>  %8s = tree.Draw(%r,%r,'gOff')"%(out,dcmd,sstring))
        nevts  = hist.Integral()
        if nevts:
          hist.Scale(1./nevts)
        hists.append(hist)
      
      # PLOT HISTOGRAMS
      print(">>> Plotting...")
      plot = Plot(xtitle,hists,clone=True)
      plot.draw(ratio=True,lstyle=1)
      plot.drawlegend()
      plot.drawtext(stitle)
      plot.saveas(pname,ext=['png']) #,'pdf'
      plot.close()
  for tree in trees:
    tree.file.Close()
  print(">>> Done.")
  
