#! /usr/bin/env python
# Author: Izaak Neutelings (May 2022)
# Description: Check GENSIM/MINIAOD for Z -> tautau -> mutau decays
# Sources:
#   http://home.thep.lu.se/~torbjorn/pythia81html/ParticleProperties.html
#   https://pdg.lbl.gov/2021/reviews/rpp2020-rev-monte-carlo-numbering.pdf
# Usage:
#   for d in `dasgoclient --query="file dataset=/DYJetsToTauTauToMuTauh_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM" --limit=2`; do echo $d; f=`basename $d`; xrdcp $XRD/$d ${f/.root/_DYJetsToTauTauToMuTauh_M-50.root}; done
#   ./convertGENSIM_mutau.py GENSIM*.root -o GENSIM_mutau.root -n 1000
#   ./convertGENSIM_mutau.py MINIAOD*.root -o MINIAOD_mutau.root -n 1000 --tdier MINIAOD
import time
start = time.time()
import os, sys, glob, copy, math
from math import log, ceil
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile, TH1F, TTree, gStyle, TH2F #, TLorentzVector
from ROOT.Math import LorentzVector
from DataFormats.FWLite import Events, Handle
import numpy as num
gStyle.SetOptStat(11111)
decaydict = { 'ele': 0, 'muon': 1, 'tau': 2 }


def convertGENSIM(infiles,outfilename,maxevts=-1,dtier='GENSIM'):
  """Loop over GENSIM events and save custom trees."""
  start1 = time.time()
  
  mothids = [23,24,25,46,9000002,9000006] # Z, W, H, LQ, ...
  
  print ">>> Loading %d input files..."%(len(infiles))
  events  = Events(infiles)
  nevents = events.size()
  print ">>> Found %s events..."%(nevents)
  assert nevents>0, "Number of entries in Events tree = %s <= 0"%(nevents)
  #exit(0)
  
  # PREPARE TREE
  print ">>> Creating output trees and branches..."
  outfile = TFile(outfilename,'RECREATE')
  tree  = TTree('event', 'event')
  tree.addBranch('nmoth',            'i')
  tree.addBranch('nmuon',            'i')
  tree.addBranch('nmuon_tau',        'i')
  tree.addBranch('ntau',             'i')
  tree.addBranch('ntau_all',         'i')
  #tree.addBranch('ntau_copy',        'i')
  tree.addBranch('ntau_hard',        'i')
  tree.addBranch('ntauh_hard',       'i')
  tree.addBranch('ntau_brem',        'i')
  #tree.addBranch('ntauh',            'i')
  tree.addBranch('moth_m',           'f')
  tree.addBranch('moth_pt',          'f')
  tree.addBranch('moth_pid',         'i')
  tree.addBranch('moth_status',      'i')
  tree.addBranch('m_ll',             'f')
  tree.addBranch('pt_ll',            'f')
  tree.addBranch('tau1_pt',          'f')
  tree.addBranch('tau1_eta',         'f')
  tree.addBranch('tau1_ncopy',       'i')
  tree.addBranch('tau2_pt',          'f')
  tree.addBranch('tau2_eta',         'f')
  tree.addBranch('tau2_ncopy',       'i')
  tree.addBranch('muon_pt',          'f')
  tree.addBranch('muon_eta',         'f')
  tree.addBranch('muon_q',           'f')
  tree.addBranch('tauh_pt',          'f')
  tree.addBranch('tauh_ptvis',       'f')
  tree.addBranch('tauh_eta',         'f')
  tree.addBranch('tauh_etavis',      'f')
  tree.addBranch('tauh_q',           'f')
  tree.addBranch('muon_tau_brem',    '?')
  tree.addBranch('muon_tau_hard',    '?')
  tree.addBranch('weight',           'f')
  
  # PREPARE HIST
  print ">>> Creating histograms..."
  h_nmoth           = TH1F('h_nmoth',          ";Number of Z bosons;Events",5,0,5)
  h_ntau_all        = TH1F('h_ntau_all',       ";Number of gen. #tau leptons (incl. copies);Events",16,0,16)
  h_ntau_all2       = TH1F('h_ntau_all2',      ";Number of gen. #tau leptons (incl. copies);Events",16,0,16)
  h_ntau_copy       = TH1F('h_ntau_copy',      ";Number of gen. #tau copies;Events",8,0,8)
  h_ntau_copy2      = TH1F('h_ntau_copy2',     ";Number of gen. #tau copies;Events",8,0,8)
  h_ntau_fromZ      = TH1F('h_ntau_fromZ',     ";Number of gen. #tau leptons from Z -> #tau#tau;Events",5,0,5)
  h_ntau_fromZ2     = TH1F('h_ntau_fromZ2',    ";Number of gen. #tau leptons from Z -> #tau#tau;Events",5,0,5)
  h_ntau_hard       = TH1F('h_ntau_hard',      ";Number of gen. #tau leptons from hard process;Events",5,0,5)
  h_ntau_prompt     = TH1F('h_ntau_prompt',    ";Number of prompt gen. #tau leptons;Events",5,0,5)
  h_ntau_brem       = TH1F('h_ntau_brem',      ";Number of gen. #tau leptons that radiate;Events",5,0,5)
  h_nelec_tau       = TH1F('h_nelec_tau',      ";Number of gen. electrons from tau decay;Events",5,0,5)
  h_nelec_prompt    = TH1F('h_nelec_prompt',   ";Number of prompt gen. electrons;Events",5,0,5)
  h_nmuon_tau       = TH1F('h_nmuon_tau',      ";Number of gen. muons from tau decay;Events",5,0,5)
  h_nmuon_tau2      = TH1F('h_nmuon_tau2',     ";Number of gen. muons from tau decay;Events with Z #rightarrow #tau#tau",5,0,5)
  h_nmuon_prompt    = TH1F('h_nmuon_prompt',   ";Number of prompt gen. muons;Events",5,0,5)
  h_tau_brem_q      = TH1F('h_tau_brem_q',     ";Gen. #tau lepton (that radiate) charge;Events",5,-2,3)
  h_muon_tau_q      = TH1F('h_muon_tau_q',     ";Gen. muons (from #tau decay) charge;Events",5,-2,3)
  h_muon_tau_q2     = TH1F('h_muon_tau_q2',    ";Gen. muons (from #tau decay) charge;Events with Z #rightarrow #tau#tau",5,-2,3)
  h_muon_tau_brem_q = TH1F('h_muon_tau_brem_q',";Gen. muons (from radiating #tau) charge;Events",5,-2,3)
  
  if 'AOD' in dtier:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'prunedGenParticles'
    handle_weight, label_weight = Handle('GenEventInfoProduct'), 'generator'
  else:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'genParticles'
    handle_weight, label_weight = Handle('GenEventInfoProduct'), 'generator'
  
  rate = 50. if '://' in infiles[0] else 100 # assume events/seconds [Hz]
  Ntot = min(maxevts,nevents) if maxevts>0 else nevents
  frac = "/%s"%(nevents) if maxevts>0 else ""
  step = stepsize(Ntot)
  print ">>> Start processing %d%s events, ETA %s (assume %d Hz)..."%(Ntot,frac,formatTimeShort(Ntot/rate),rate)
  start_proc = time.time()
  
  # LOOP OVER EVENTS
  evtid = 0
  npass = 0
  for event in events:
    #print '='*30
    #print evtid
    if maxevts>0 and evtid>=maxevts:
      break
    if evtid>0 and evtid%step==0:
      ETA, rate = getETA(start_proc,evtid+1,Ntot)
      print ">>>   Processed %4s/%d events, ETA %s (%d Hz)"%(evtid,Ntot,ETA,rate)
    evtid += 1
    
    # GET BRANCHES
    event.getByLabel(label_gps,handle_gps) # genparticles
    gps = handle_gps.product()
    event.getByLabel(label_weight,handle_weight) # gen weight
    
    # GEN PARTICLES
    gps_final     = [p for p in gps if isFinal(p) and abs(p.pdgId()) in [5,6,11,12,13,14,15,16]+mothids]
    #gps_final     = [p for p in gps if p.isLastCopy() and abs(p.pdgId()) in [5,6,11,12,13,14,15,16]+mothids]
    #gps_final     = [p for p in gps if p.isFirstCopy() and abs(p.pdgId()) in [5,6,11,12,13,14,15,16]+mothids]
    gps_mother    = [p for p in gps_final if abs(p.pdgId()) in mothids and p.status()>60]
    gps_tau_all   = [p for p in gps if abs(p.pdgId())==15]
    gps_tau       = [p for p in gps_final if abs(p.pdgId())==15 and p.status()==2] # exclude radiating taus
    gps_tau_brem  = [p for p in gps_final if abs(p.pdgId())==15 and any(abs(p.daughter(i).pdgId())==22 for i in range(p.numberOfDaughters()))]
    gps_muons     = [p for p in gps_final if abs(p.pdgId())==13 and p.isLastCopy()]
    gps_muons_tau = [m for m in gps_muons if m.statusFlags().isDirectHardProcessTauDecayProduct()]
    gps_elecs     = [p for p in gps_final if abs(p.pdgId())==11 and p.isLastCopy()]
    gps_elecs_tau = [e for e in gps_elecs if e.statusFlags().isDirectHardProcessTauDecayProduct()]
    #gps_muons_tau = [m for m in gps_muons if m.statusFlags().isDirectHardProcessTauDecayProduct()]
    
    # TAU WITH FSR
    gps_tau_brem = [ ]
    for tau in gps_tau:
      moth = tau
      while moth.numberOfMothers()>=1 and abs(moth.pdgId())==15:
        for i in range(moth.numberOfMothers()):
          if abs(moth.mother(i).pdgId())==15:
            moth = moth.mother(i)
            break
        else:
          break # none of mothers is tau
        if any(abs(moth.daughter(i).pdgId())==22 for i in range(moth.numberOfDaughters())):
          gps_tau_brem.append(tau)
          break
    
    # COUNT TAU COPIES
    for tau in gps_tau:
      ncopy = 1
      moth = tau
      while moth.numberOfMothers()>=1 and abs(moth.pdgId())==15:
        for i in range(moth.numberOfMothers()):
          if abs(moth.mother(i).pdgId())==15:
            moth = moth.mother(i)
            ncopy += 1
            break
        else:
          break # none of mothers is tau
      tau.ncopy = ncopy # save for later
      h_ntau_copy.Fill(ncopy)
    
    # HISTOGRAMS
    h_nmoth.Fill(len(gps_mother))
    h_ntau_all.Fill(len(gps_tau_all))
    h_ntau_hard.Fill(sum(t.statusFlags().fromHardProcess() for t in gps_tau)) # fill before selecting events
    h_ntau_prompt.Fill(sum(t.statusFlags().isPrompt() and t.statusFlags().isLastCopy() for t in gps_tau)) # fill before selecting events
    h_ntau_brem.Fill(len(gps_tau_brem)) # count radiated photons
    h_nelec_tau.Fill(len(gps_elecs_tau)) # fill before selecting events
    h_nelec_prompt.Fill(sum(e.statusFlags().isPrompt() and e.statusFlags().isLastCopy() for t in gps_elecs)) # fill before selecting events
    h_nmuon_tau.Fill(len(gps_muons_tau)) # fill before selecting events
    h_nmuon_prompt.Fill(sum(m.statusFlags().isPrompt() and m.statusFlags().isLastCopy() for m in gps_muons)) # fill before selecting events
    for muon in gps_muons_tau:
      h_muon_tau_q.Fill(muon.charge()) #-muon.pdgId()/13
    for tau in gps_tau_brem:
      h_tau_brem_q.Fill(tau.charge())
      dau = getdaughter_tau(tau)
      if abs(dau.pdgId())==13: # muon
        h_muon_tau_brem_q.Fill(dau.charge())
    
    # REQUIRE Z BOSON
    gps_tau_fromZ = [ ]
    moth = None
    if gps_mother:
      moth = gps_mother[-1] # take last one
      gps_tau_fromZ = [t for t in gps_tau if getmother(t)==moth] # requires on-shell Z boson
    h_ntau_fromZ.Fill(len(gps_tau_fromZ))
    ###if not gps_mother:
    ###  continue # only look at events with Z bosons
    
    # TAUS
    #gps_tau_hard = [t for t in gps_tau if t.mother(0)==moth] # does not include radiating taus
    #gps_tau_hard = [t for t in gps_tau if getmother(t)==moth] # requires on-shell Z boson
    gps_tau_hard = [t for t in gps_tau if t.statusFlags().fromHardProcess()]
    if len(gps_tau_hard)<2:
      #if len(gps_tau)>=2:
      #  print '-'*8 + " no Z -> taus ?"
      #  print ">>> Z BOSON:"
      #  for part in gps_final:
      #    if abs(part.pdgId()) in mothids:
      #      printParticle(part)
      #  print ">>> TAUS:"
      #  for tau in gps_tau:
      #    printParticle(tau.mother(0))
      #    printParticle(tau)
      print ">>> %5d: Failed pre-selection: %s tau leptons from tau decay..."%(evtid,len(gps_tauh_hard))
      continue # only look at events from hard process pp -> (Z ->) tautau
    if len(gps_tau_fromZ)>=2:
      h_ntau_fromZ2.Fill(len(gps_tau_fromZ)) # fill for Z -> tautau
      h_nmuon_tau2.Fill(len(gps_muons_tau)) # fill for Z -> tautau
      for muon in gps_muons_tau:
        h_muon_tau_q2.Fill(muon.charge())
    ###if len(gps_tau_fromZ)<1:
    ###  print '-'*80
    ###  for tau in gps: # look for gluon initiated processes
    ###    if abs(tau.pdgId())!=15: continue
    ###    if tau.numberOfMothers()<=1: continue
    ###    if any(abs(tau.mother(i).pdgId())==15 for i in range(tau.numberOfMothers())): continue
    ###    #if not any(abs(tau.mother(i).pdgId())==21 for i in range(tau.numberOfMothers())): continue
    ###    #if tau.mother(0).pdgId()==-tau.mother(1).pdgId(): continue
    ###    #print ">>> %5s -> %s"%(' '.join(str(tau.mother(i).pdgId()) for i in range(tau.numberOfMothers())),tau.pdgId())
    ###    print ">>> %5s -> %s"%(' '.join(str(tau.mother(i).pdgId()) for i in range(tau.numberOfMothers())),
    ###                           ' '.join(str(tau.mother(0).daughter(i).pdgId()) for i in range(tau.mother(0).numberOfDaughters())))
    ###    ###print getprodchain(tau)
    ###    ###for i in range(tau.numberOfMothers()):
    ###    ###  tmoth = tau.mother(i)
    ###    ###  print getprodchain(tmoth)
    ###    ###  print ">>> %5s -> %s"%(' '.join(str(tau.mother(i).pdgId()) for i in range(tau.numberOfMothers())),
    ###    ###                         ' '.join(str(tmoth.daughter(i).pdgId()) for i in range(tmoth.numberOfDaughters())))
    ###  ###for tau in gps_tau_hard:
    ###  ###  #printParticle(tau)
    ###  ###  print getprodchain(tau)
    
    # MUONS
    ###if gps_muons:
    ###  print '-'*80
    ###  for muon in gps_muons:
    ###    for i in range(muon.numberOfDaughters()):
    ###      if abs(muon.daughter(i).pdgId())==13:
    ###        printParticle(muon)
    ###        getprodchain(muon)
    if len(gps_muons_tau)<1:
      ###print ">>> %5d: Failed pre-selection: %s muons from tau decay..."%(evtid,len(gps_muons_tau))
      continue # only look at events with Z -> tautau -> mutau
    
    # VETO TAU -> ELECTRONS DECAYS
    if len(gps_elecs_tau)>=1:
      ###print ">>> %5d: Failed pre-selection: found electrons from tau decay..."%(evtid)
      ###for particle in gps_muons_tau+gps_elecs_tau+gps_tau_hard:
      ###  #printParticle(particle)
      ###  print getprodchain(particle)
      continue
    
    # NON-LEPTONIC TAUS
    #gps_tauh_hard = [t for t in gps_tau_hard if not any(abs(t.daughter(i).pdgId())<16 for i in range(t.numberOfDaughters()))]
    gps_tauh_hard = [t for t in gps_tau_hard if not any(abs(t.daughter(i).pdgId()) in [11,12,13,14,15] for i in range(t.numberOfDaughters()))]
    if len(gps_tauh_hard)<1:
      ###print ">>> %5d: Failed pre-selection: %s tauh from tau decay..."%(evtid,len(gps_tauh_hard))
      continue # only look at events with Z -> tautau -> mutau
    muon_tau = gps_muons_tau[0]
    tauh_hard = gps_tauh_hard[0]
    h_ntau_all2.Fill(len(gps_tau_all))
    for tau in gps_tau_hard:
      h_ntau_copy2.Fill(tau.ncopy)
    
    #### CHECK FOR MUTAU
    ###muon_tau = None
    ###tauh_hard = None
    ###skip     = False
    ###for tau in gps_tau_hard:
    ###  for i in range(moth.numberOfDaughters()):
    ###    dau = tau.daughter(i)
    ###    assert abs(dau.pdgId())!=15 # should already be final copy
    ###    ###while abs(dau.pdgId())==15: # unlikely
    ###    ###  dau = dau.daughter(0)
    ###    if abs(dau.pdgId())==13: # muonic decay
    ###      if muon_tau: skip = True; break # tautau -> mumu: require only one muon
    ###      muon_tau = dau
    ###      break # check next tau
    ###    elif abs(dau.pdgId())>20: # non-leptonic decay
    ###      if tauh_hard: skip = True; break # tautau -> tauhtauh: require only one tauh
    ###      tauh_hard = tau
    ###      break # check next tau
    ###  else: # no break: did not find muon or non-leptonic decay
    ###    skip = True; break
    ###  if skip:
    ###    break
    ###if skip or not muon_tau or not tauh_hard: # failed mutau requirement
    ###  continue
    
    tauh_p4vis = p4svis(tauh_hard)
    Zp4 = gps_tau_hard[0].p4()+gps_tau_hard[1].p4() # Z boson four momentum
    gps_tau.sort(key=lambda p: p.pt(),reverse=True)
    gweight                  = handle_weight.product()
    tree.weight[0]           = gweight.weight()
    tree.nmoth[0]            = len(gps_mother)
    if moth:
      tree.moth_pid[0]       = moth.pdgId()
      tree.moth_status[0]    = moth.status()
      tree.moth_m[0]         = moth.mass()
      tree.moth_pt[0]        = moth.pt()
    else:
      tree.moth_pid[0]       = 0
      tree.moth_status[0]    = 0
      tree.moth_m[0]         = -1
      tree.moth_pt[0]        = -1
    tree.m_ll[0]             = Zp4.M()
    tree.pt_ll[0]            = Zp4.Pt()
    tree.nmuon[0]            = len(gps_muons)
    tree.nmuon_tau[0]        = len(gps_muons_tau)
    tree.ntau[0]             = len(gps_tau)
    tree.ntau_all[0]         = len(gps_tau_all)
    tree.ntau_hard[0]        = len(gps_tau_hard)
    tree.ntauh_hard[0]       = len(gps_tauh_hard)
    tree.ntau_brem[0]        = len(gps_tau_brem)
    tree.tau1_pt[0]          = gps_tau[0].pt()
    tree.tau1_eta[0]         = gps_tau[0].eta()
    tree.tau1_ncopy[0]       = gps_tau[0].ncopy
    tree.tau2_pt[0]          = gps_tau[1].pt()
    tree.tau2_eta[0]         = gps_tau[1].eta()
    tree.tau2_ncopy[0]       = gps_tau[1].ncopy
    tree.muon_pt[0]          = muon_tau.pt()
    tree.muon_eta[0]         = muon_tau.eta()
    tree.muon_q[0]           = muon_tau.charge() # -muon_tau.pdgId()/13
    tree.muon_tau_brem[0]    = getmother(muon_tau) in gps_tau_brem
    tree.muon_tau_hard[0]    = muon_tau.statusFlags().isDirectHardProcessTauDecayProduct()
    tree.tauh_pt[0]          = tauh_hard.pt()
    tree.tauh_eta[0]         = tauh_hard.eta()
    tree.tauh_ptvis[0]       = tauh_p4vis.pt()
    tree.tauh_etavis[0]      = tauh_p4vis.eta()
    tree.tauh_q[0]           = tauh_hard.charge() # -tauh_hard.pdgId()/15
    tree.Fill()
    npass += 1
  
  # npass = tree.GetEntries()
  print ">>> Processed %4s events in %s"%(evtid,formatTime(time.time()-start_proc))
  print ">>> Selected %5s / %4s events (%d%%)"%(npass,evtid,(100.0*npass/evtid) if evtid else 0)
  print ">>> Writing to output file %s..."%(outfilename)
  outfile.Write()
  outfile.Close()
  

root_dtype = { # python/numpy -> root data type
  '?': 'O',  'bool':    'O',  bool:   'O', # Bool_t  
  'b': 'b',  'int8':    'b',  'byte': 'b', # UChar_t 
  'i': 'I',  'int32':   'I',               # Int_t   
  'l': 'L',  'int64':   'L',  int:    'L', # Long64_t
  'f': 'F',  'float32': 'F',               # Float_t 
  'd': 'D',  'float64': 'D',  float:  'D', # Double_t
}


def addBranch(self, name, dtype='f', default=None):
   """Add branch with a given name, and create an array of the same name as address."""
   # https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/TreeProducer.py
   if hasattr(self,name):
     raise IOError("TTree.addBranch: Branch of name '%s' already exists!"%(name))
   if isinstance(dtype,str):
     if dtype.lower()=='f': # 'f' is only a 'float32', and 'F' is a 'complex64', which do not work for filling float branches
       dtype = float        # float is a 'float64' ('f8')
     elif dtype.lower()=='i': # 'i' is only a 'int32'
       dtype = int            # int is a 'int64' ('i8')
   setattr(self,name,num.zeros(1,dtype=dtype))
   self.Branch(name, getattr(self,name), '%s/%s'%(name,root_dtype[dtype]))
   if default!=None:
     getattr(self,name)[0] = default
TTree.addBranch = addBranch


#def p4sumvis(particles):
#  #import pdb; pdb.set_trace()
#  visparticles = copy.deepcopy([p for p in particles if abs(p.pdgId()) not in [12,14,16]])
#  p4 = visparticles[-1].p4() if particles else 0.
#  visparticles.pop()
#  for p in visparticles:
#    p4 += p.p4()
#  return p4
  

def p4svis(particle):
  p4vis = LorentzVector('ROOT::Math::PtEtaPhiM4D<double>')(0,0,0,0)  #LorentzVector(0,0,0,0)
  for i in range(particle.numberOfDaughters()):
    if abs(particle.daughter(i).pdgId()) in [12,14,16]:
      continue
    if particle.daughter(i).pdgId()==particle.pdgId():
      p4vis += p4svis(particle.daughter(i)) # recursive
    else:
      p4vis += particle.daughter(i).p4() # assume no invisible decays of daughter
  return p4vis
  

def finalDaughters(particle, daughters):
  """Fills daughters with all the daughters of particle recursively."""
  if particle.numberOfDaughters()==0:
    daughters.append(particle)
  else:
    foundDaughter = False
    for i in range(particle.numberOfDaughters()):
      dau = particle.daughter(i)
      if dau.status()>=1:
        daughters = finalDaughters(dau,daughters)
        foundDaughter = True
    if not foundDaughter:
      daughters.append(particle)
  return daughters
  

def isFinal(p): # Warning! Can still include radiation
  return not (p.numberOfDaughters()==1 and p.daughter(0).pdgId()==p.pdgId())
  

def getmother(p):
  """Get mother, which does not have the same PDG ID."""
  if p.numberOfMothers()<1:
    return None
  for i in range(p.numberOfMothers()):
    if p.mother(i).pdgId()==p.pdgId():
      return getmother(p.mother(i))
  return p.mother(0)
  

def getdaughter_tau(particle):
  for i in range(particle.numberOfDaughters()):
    dau = particle.daughter(i)
    pid = abs(dau.pdgId())
    if pid==15:
      return getdaughter_tau(dau)
    elif pid in [12,14,16]:
      continue # ignore neutrinos
    else:
      return dau # assume hadron or charged lepton
  return None
  

def getprodchain(particle):
  """Print productions chain."""
  chain = "%3s"%(particle.pdgId())
  while particle.numberOfMothers()>0:
    particle = particle.mother(0)
    chain = "%3s -> "%(particle.pdgId())+chain
  return chain
  

def printParticle(p):
  string = "%9d: status=%2d, pt=%7.2f, eta=%5.2f, phi=%5.2f, final=%5s"%(p.pdgId(),p.status(),p.pt(),p.eta(),p.phi(),isFinal(p))
  if p.numberOfMothers()>=2:
    string += ", mothers "+', '.join(str(p.mother(i).pdgId()) for i in range(p.numberOfMothers()))
  elif p.numberOfMothers()==1:
    string += ", mother %s"%(p.mother(0).pdgId())
  if p.numberOfDaughters()>=2:
    string += ", daughters "+', '.join(str(p.daughter(i).pdgId()) for i in range(p.numberOfDaughters()))
  elif p.numberOfDaughters()==1:
    string += ", daughter %s"%(p.daughter(0).pdgId())
  print string
  

def formatTime(seconds):
  minutes, seconds = divmod(seconds, 60)
  hours,   minutes = divmod(minutes, 60)
  if   hours:   return "%d hours, %d minutes and %.3g seconds"%(hours,minutes,seconds)
  elif minutes: return "%d minutes and %.3g seconds"%(minutes,seconds)
  return "%.3g seconds"%(seconds)
  

def formatTimeShort(seconds):
  minutes, seconds = divmod(seconds, 60)
  hours,   minutes = divmod(minutes, 60)
  return "%02d:%02d:%02d"%(hours,minutes,seconds)
  

def bold(string):
  return "\033[1m%s\033[0m"%(string)
  

def stepsize(total):
  """Help function to compute reasonable stepsize for print out."""
  return min(max(10**(ceil(log(total,10))-1),20),2000)
  

def getETA(start,iJob,nJobs):
  """Help function to compute ETA and event rate."""
  dt   = time.time()-start
  rate = iJob/dt # events/seconds [Hz]
  ETA  = formatTimeShort((nJobs-iJob)/rate)
  return ETA, rate
  

def ensuredir(dir):
  if not os.path.exists(dir):
    os.makedirs(dir)
    print ">>> Made directory %s\n>>>"%(dir)
  return dir
  

def main(args):
  
  # SETTING
  url       = args.url #'root://t3dcachedb.psi.ch:1094/'
  outdir    = args.outdir or ""
  maxevts   = args.maxevts
  tag       = args.tag
  dtier     = args.dtier
  verbosity = args.verbosity
  infiles   = args.infiles
  outfile   = args.outfile
  
  # INPUT FILES
  if infiles:
    if len(infiles)==1 and not infiles[0].lower().endswith('.root'):
      with open(infiles[0],'r') as infile:
        infiles = [l.strip() for l in infile if l.strip().endswith('.root')]
    elif url: # prepend director URL
      infiles = [(url+f if '://' not in f else f) for f in infiles]
  else:
    raise IOError("No input given to run on.")
  
  # OUTPUT FILE
  if outfile:
    outdir2 = os.path.dirname(outfile)
    outfile = os.path.basename(outfile) # remove any directory
    if outdir2:
      outdir = os.path.join(outdir,outdir2) # add to user output directory
  else:
    outfile = infiles[0].split('/')[-1]
    if 'GENSIM' in outfile:
      outfile = outfile[:outfile.rfind('GENSIM')]+"GENSIM_simple%s.root"%tag
    else:
      outfile = outfile.replace(".root","_simple%s.root"%tag)
  if outdir:
    ensuredir(outdir)
    outfile = os.path.join(outdir,outfile)
  
  # CONVERT
  if len(infiles)<=10 or verbosity>=1:
    print ">>> Input files:"
    for file in infiles:
      print ">>>   %s"%(file)
  else:
    nshow = min(len(infiles),10)
    print ">>> Input files: (showing %d/%d)"%(nshow,len(infiles))
    for file in infiles[:nshow]:
      print ">>>   %s"%(file)
  print ">>> Output file: %s"%(outfile)
  convertGENSIM(infiles,outfile,maxevts=maxevts,dtier=dtier)
  print ">>> Done in in %s"%(formatTime(time.time()-start))
  

if __name__=='__main__':
  from argparse import ArgumentParser
  usage = """Convert CMSSW GENSIM/MINIAO files to a simplified format for generator-level analysis."""
  parser = ArgumentParser(prog="convertGENSIM",description=usage,epilog="Succes!")
  parser.add_argument('infiles',        nargs='+',
                      metavar='FILE',   help="(text file of) GENSIM ROOT files to simplify")
  parser.add_argument('-o','--outfile',
                      metavar='FILE',   help="output file" )
  parser.add_argument('-d','--outdir',  help="output direcory (create if does not exist)")
  parser.add_argument('-D','--dtier',   choices=['GENSIM','MINIAOD'], default='GENSIM',
                                        help="CMSSW data tier, default=%(default)r")
  parser.add_argument('-n','--maxevts', type=int,default=-1,
                                        help="maximum number of event to process")
  parser.add_argument('-u','--url',     default=None,
                                        help="extra URL to prepend input files, e.g. root://cms-xrd-global.cern.ch/")
  parser.add_argument('-t','--tag',     default="",
                                        help="extra tag for output")
  parser.add_argument('-v','--verbose', dest='verbosity',type=int,nargs='?',const=1,default=0,
                                        help="set verbosity level") # add at end of options
  args = parser.parse_args()
  main(args)
  #print ">>> Done"
  

