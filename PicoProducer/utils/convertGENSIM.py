#! /usr/bin/env python
# Author: Yuta Takahashi, Izaak Neutelings
# Description: Converts GENSIM/MINIAOD sample to a simplified format for generator-level analysis
# Sources:
#   http://home.thep.lu.se/~torbjorn/pythia81html/ParticleProperties.html
#   https://pdg.lbl.gov/2021/reviews/rpp2020-rev-monte-carlo-numbering.pdf
# Usage:
#   ./convertGENSIM.py GENSIM*.root -o GENSIM_simple.root -n 1000
#   ./convertGENSIM.py MINIAOD*.root -o MINIAOD_simple.root -n 1000 -dtier MINIAOD
#   ./convertGENSIM.py GENSIM.txt GENSIM_simple.root -n 1000
import time
start = time.time()
import os, sys, glob, copy, math
from math import log, ceil
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TFile, TH1F, TTree, gStyle, TH2F
from DataFormats.FWLite import Events, Handle
import numpy as num
gStyle.SetOptStat(11111)
decaydict = { 'ele': 0, 'muon': 1, 'tau': 2 }


def convertGENSIM(infiles,outfilename,maxevts=-1,isPythia=False,dtier='GENSIM'):
  """Loop over GENSIM events and save custom trees."""
  start1 = time.time()
  
  mothids = [23,24,25,46,9000002,9000006] # Z, W, H, LQ, ...
  
  print ">>> Loading %d input files..."%(len(infiles))
  events  = Events(infiles)
  assert events.size()>0, "Number of entries in Events tree = %s <= 0"%(events.size())
  outfile = TFile(outfilename,'RECREATE')
  
  print ">>> Creating output trees and branches..."
  tree_event  = TTree('event', 'event')
  tree_jet    = TTree('jet',   'jet')
  tree_mother = TTree('mother','mother')
  tree_decay  = TTree('decay', 'decay') 
  tree_assoc  = TTree('assoc', 'assoc')
  
  # EVENT
  tree_event.addBranch('nbgen',       'i')
  tree_event.addBranch('nbcut',       'i')
  tree_event.addBranch('ntgen',       'i')
  tree_event.addBranch('njet',        'i')
  tree_event.addBranch('nlepton',     'i')
  tree_event.addBranch('ntau',        'i')
  tree_event.addBranch('ntaucut',     'i')
  tree_event.addBranch('nnu',         'i')
  tree_event.addBranch('nmoth',       'i')
  tree_event.addBranch('ntau_assoc',  'i')
  tree_event.addBranch('ntau_decay',  'i')
  tree_event.addBranch('nbgen_decay', 'i')
  tree_event.addBranch('met',         'f')
  tree_event.addBranch('jpt1',        'f')
  tree_event.addBranch('jpt2',        'f')
  tree_event.addBranch('sumjet',      'f')
  tree_event.addBranch('dphi_jj',     'f')
  tree_event.addBranch('deta_jj',     'f')
  tree_event.addBranch('dr_jj',       'f')
  tree_event.addBranch('ncentral',    'i')
  tree_event.addBranch('mjj',         'f')
  tree_event.addBranch('moth1_mass',  'f')
  tree_event.addBranch('moth2_mass',  'f')
  tree_event.addBranch('moth1_pt',    'f')
  tree_event.addBranch('moth2_pt',    'f')
  tree_event.addBranch('tau1_pt',     'f')
  tree_event.addBranch('tau1_eta',    'f')
  tree_event.addBranch('tau2_pt',     'f')
  tree_event.addBranch('tau2_eta',    'f')
  tree_event.addBranch('st',          'f') # scalar sum pT
  tree_event.addBranch('stmet',       'f') # scalar sum pT with MET
  tree_event.addBranch('weight',      'f')
  
  # MOTHER DECAY
  tree_mother.addBranch('pid',        'i')
  tree_mother.addBranch('moth',       'i')
  tree_mother.addBranch('status',     'i')
  tree_mother.addBranch('pt',         'f')
  tree_mother.addBranch('eta',        'f')
  tree_mother.addBranch('phi',        'f')
  tree_mother.addBranch('mass',       'f')
  tree_mother.addBranch('inv',        'f')
  tree_mother.addBranch('ndau',       'i')
  tree_mother.addBranch('dau',        'i')
  tree_mother.addBranch('dphi_ll',    'f')
  tree_mother.addBranch('deta_ll',    'f')
  tree_mother.addBranch('dr_ll',      'f')
  tree_mother.addBranch('st',         'f') # scalar sum pT
  tree_mother.addBranch('stmet',      'f') # scalar sum pT with MET
  tree_mother.addBranch('weight',     'f')
  
  # FROM MOTHER DECAY
  tree_decay.addBranch('pid',         'i')
  tree_decay.addBranch('pt',          'f')
  tree_decay.addBranch('eta',         'f')
  tree_decay.addBranch('phi',         'f')
  tree_decay.addBranch('mass',        'f')
  tree_decay.addBranch('ptvis',       'f')
  tree_decay.addBranch('type',        'i')
  tree_decay.addBranch('isBrem',      'i')
  tree_decay.addBranch('weight',      'f')
  
  # NOT FROM MOTHER DECAY (ASSOCIATED)
  tree_assoc.addBranch('pid',         'i')
  tree_assoc.addBranch('moth',        'i')
  tree_assoc.addBranch('pt',          'f')
  tree_assoc.addBranch('ptvis',       'f')
  tree_assoc.addBranch('eta',         'f')
  tree_assoc.addBranch('phi',         'f')
  tree_assoc.addBranch('weight',      'f')
  
  # JETS
  tree_jet.addBranch('pt',            'f')
  tree_jet.addBranch('eta',           'f')
  tree_jet.addBranch('phi',           'f')
  tree_jet.addBranch('weight',        'f')
  
  # HISTOGRAMS
  hist_moth_decay = TH1F('moth_decay',"mother decay",60,-30,30)
  
  if 'AOD' in dtier:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'prunedGenParticles'
    handle_jets,   label_jets   = Handle('std::vector<reco::GenJet>'), 'slimmedGenJetsAK8'
    handle_met,    label_met    = Handle('vector<reco::GenMET>'), 'genMetTrue'
    handle_weight, label_weight = Handle('GenEventInfoProduct'), 'generator'
  else:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'genParticles'
    handle_jets,   label_jets   = Handle('std::vector<reco::GenJet>'), 'ak4GenJets'
    handle_met,    label_met    = Handle('vector<reco::GenMET>'), 'genMetTrue'
    handle_weight, label_weight = Handle('GenEventInfoProduct'), 'generator'
  
  evtid = 0
  rate = 50. if '://' in infiles[0] else 100 # assume events/seconds [Hz]
  Ntot = min(maxevts,events.size()) if maxevts>0 else events.size()
  frac = "/%s"%(events.size()) if maxevts>0 else ""
  step = stepsize(Ntot)
  print ">>> Start processing %d%s events, ETA %s (assume %d Hz)..."%(Ntot,frac,formatTimeShort(Ntot/rate),rate)
  start_proc = time.time()
  
  # LOOP OVER EVENTS
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
    event.getByLabel(label_jets,handle_jets) # gen jets
    jets = handle_jets.product()
    event.getByLabel(label_met,handle_met) # gen met
    met = handle_met.product()
    event.getByLabel(label_weight,handle_weight) # gen weight
    gweight = handle_weight.product()
    weight = gweight.weight()
    
    # GEN PARTICLES
    gps_mother = [p for p in gps if isFinal(p) and abs(p.pdgId()) in [42]]
    gps_final  = [p for p in gps if isFinal(p) and abs(p.pdgId()) in [5,6,15,16]+mothids]
    gps_mother = [p for p in gps_final if abs(p.pdgId()) in mothids and p.status()>60] #not(moth.numberOfDaughters()==2 and abs(moth.daughter(0).pdgId()) in mothids)
    gps_bgen   = [p for p in gps_final if abs(p.pdgId())==5 and p.status()==71]
    gps_bcut   = [p for p in gps_bgen  if p.pt()>20 and abs(p.eta())<2.5]
    gps_tgen   = [p for p in gps_final if abs(p.pdgId())==6] #[-1:]
    gps_nugen  = [p for p in gps_final if abs(p.pdgId())==16]
    gps_tau    = [p for p in gps_final if abs(p.pdgId())==15 and p.status()==2]
    gps_tau.sort(key=lambda p: p.pt(), reverse=True)
    gps_taucut = [p for p in gps_tau   if p.pt()>20 and abs(p.eta())<2.5]
    
    #print '-'*10
    #for p in gps_tgen:
    #  printParticle(p)
    #if gps_tgen:
    #  print "has top"
    #for p in gps_nugen:
    #  printParticle(p)
    
    # REMOVE TOP QUARK if its final daughter is also in the list
    for top in gps_tgen[:]:
      dau = top
      while abs(dau.daughter(0).pdgId())==6:
        dau = dau.daughter(0)
      if dau!=top and dau in gps_tgen:
        gps_tgen.remove(top)
    
    # REMOVE JET-LEPTON OVERLAP
    jets, dummy = cleanObjectCollection(jets,gps_tau,dRmin=0.5)
    njets  = 0
    sumjet = 0
    jets30  = [ ]
    for jet in jets:
      if jet.pt()>30 and abs(jet.eta())<5:
        sumjet            += jet.pt()
        njets             += 1
        tree_jet.pt[0]     = jet.pt()
        tree_jet.eta[0]    = jet.eta()
        tree_jet.phi[0]    = jet.phi()
        tree_jet.weight[0] = weight
        tree_jet.Fill()
        jets30.append(jet)
    
    # MULTIPLICITIES
    tree_event.nmoth[0]   = len(gps_mother)
    tree_event.nbcut[0]   = len(gps_bcut)
    tree_event.nbgen[0]   = len(gps_bgen)
    tree_event.ntgen[0]   = len(gps_tgen)
    tree_event.njet[0]    = njets
    tree_event.nlepton[0] = len(gps_tau)
    tree_event.ntau[0]    = len(gps_tau)
    tree_event.ntaucut[0] = len(gps_taucut)
    tree_event.nnu[0]     = len(gps_nugen)
    
    # JETS
    tree_event.met[0]     = met[0].pt()
    tree_event.sumjet[0]  = sumjet
    if len(jets30)>=2:
      centrajpt1s = findCentrajpt1s(jets30[:2],jets30[2:])
      tree_event.ncentral[0] = len(centrajpt1s)
    else:
      tree_event.ncentral[0] = -9
    if(len(jets30)>=2):
      tree_event.jpt1[0]    = jets30[0].pt()
      tree_event.jpt2[0]    = jets30[1].pt()    
      tree_event.dphi_jj[0] = deltaPhi(jets30[0].phi(), jets30[1].phi())
      tree_event.deta_jj[0] = jets30[0].eta() - jets30[1].eta()
      tree_event.dr_jj[0]   = deltaR(jets30[0].eta(),jets30[0].phi(),jets30[1].eta(),jets30[1].phi())
      dijetp4               = jets30[0].p4() + jets30[1].p4()
      tree_event.mjj[0]     = dijetp4.M()
    elif (len(jets30)==1):
      tree_event.jpt1[0]    = jets30[0].pt()
      tree_event.jpt2[0]    = -1
      tree_event.dphi_jj[0] = -9
      tree_event.deta_jj[0] = -9
      tree_event.dr_jj[0]   = -1
      tree_event.mjj[0]     = -1
    else:
      tree_event.jpt1[0]    = -1
      tree_event.jpt2[0]    = -1
      tree_event.dphi_jj[0] = -9
      tree_event.deta_jj[0] = -9
      tree_event.dr_jj[0]   = -1
      tree_event.mjj[0]     = -1
    
    # SCALAR SUM PT
    if len(gps_taucut)>=2 and len(gps_bcut)>=1:
      st = 0
      #gps_taucut.sort(key=lambda p: p.pt(), reverse=True)
      gps_bcut.sort(key=lambda p: p.pt(), reverse=True)
      #taus_assoc.sort(key=lambda p: p.pt(), reverse=True)
      #taus_decay.sort(key=lambda p: p.pt(), reverse=True)
      #bgen_decay.sort(key=lambda p: p.pt(), reverse=True)
      for part in gps_taucut[2:]+gps_bcut[1:]:
        st += part.pt()
      stmet = st + met[0].pt()
    else:
      st    = -1
      stmet = -1
    tree_event.tau1_pt[0]   = gps_tau[0].pt()
    tree_event.tau1_eta[0]  = gps_tau[0].eta()
    tree_event.tau2_pt[0]   = gps_tau[1].pt()
    tree_event.tau2_eta[0]  = gps_tau[1].eta()
    tree_event.st[0]        = st
    tree_event.stmet[0]     = stmet
    tree_mother.st[0]       = st
    tree_mother.stmet[0]    = stmet
    
    tree_event.weight[0] = weight
    
    # TAU
    taus_assoc = [ ]
    for gentau in gps_tau:
      
      while gentau.status()!=2:
        gentau = gentau.daughter(0)
      genfinDaughters = finalDaughters(gentau, [])
      genptvis = p4sumvis(genfinDaughters).pt()
      
      # CHECK MOTHER
      taumoth   = gentau.mother(0)
      mothpid   = abs(taumoth.pdgId())
      from_moth = False
      #from_had = False # from hadron decay
      #print '-'*30
      while mothpid!=2212: # proton
        #print taumoth.pdgId()
        if mothpid in mothids:
          from_moth = True
          break
        elif 100<mothpid<10000: #and mothpid!=2212:
          #from_had = True
          break
        taumoth = taumoth.mother(0)
        mothpid = abs(taumoth.pdgId())
      
      # ASSOC
      if not from_moth:
        tree_assoc.pt[0]     = gentau.pt()
        tree_assoc.ptvis[0]  = genptvis
        tree_assoc.eta[0]    = gentau.eta()
        tree_assoc.phi[0]    = gentau.phi()
        tree_assoc.pid[0]    = gentau.pdgId()
        tree_assoc.moth[0]   = taumoth.pdgId()
        tree_assoc.weight[0] = weight
        tree_assoc.Fill()
        #if not from_had:
        taus_assoc.append(gentau)
    
    # B QUARK
    for genb in gps_bgen:
      bmoth   = genb.mother(0)
      mothpid = abs(bmoth.pdgId())
      from_moth = False
      while mothpid!=2212:
        if mothpid in mothids:
          from_moth = True
          break
        bmoth   = bmoth.mother(0)
        mothpid = abs(bmoth.pdgId())
      if not from_moth:
        tree_assoc.pt[0]     = genb.pt()
        tree_assoc.ptvis[0]  = -1
        tree_assoc.eta[0]    = genb.eta()
        tree_assoc.phi[0]    = genb.phi()
        tree_assoc.pid[0]    = genb.pdgId()
        tree_assoc.moth[0]   = bmoth.pdgId()
        tree_assoc.weight[0] = weight
        tree_assoc.Fill()
    
    # MOTHER
    #print '-'*80
    taus_decay = [ ]
    bgen_decay = [ ]
    gps_mother.sort(key=lambda p: p.pt(), reverse=True)
    for moth in gps_mother:
      
      dau_pid = 0
      pair    = [ ]
      
      if moth.numberOfDaughters()==2:
        if moth.daughter(0).pdgId() in [21,22] or moth.daughter(1).pdgId() in [21,22]:
          continue
        if abs(moth.daughter(0).pdgId()) in mothids: # single production with t-channel LQ
          continue
      
      granma = moth.mother(0) # grand mother
      while abs(granma.pdgId()) in mothids:
        granma = granma.mother(0)
      
      for i in range(moth.numberOfDaughters()):
        #print '\t', dau.pdgId()
        dau = moth.daughter(i)
        
        # TAU
        isBrem = False
        if abs(dau.pdgId())==15:
          while dau.status()!=2:
            dau = dau.daughter(0)
          if dau.numberOfDaughters()==2 and abs(dau.daughter(0).pdgId())==15 and dau.daughter(1).pdgId()==22:
              #print "This is brems !?!"
              isBrem = True
          else:
            taus_decay.append(dau)
        
        # BOTTOM QUARK
        elif abs(dau.pdgId())==5:
          dau_pid = dau.pdgId()
          bgen_decay.append(dau)
        
        # TOP QUARK
        elif abs(dau.pdgId())==6:
          dau_pid = dau.pdgId()
          newdau = dau
          while abs(newdau.daughter(0).pdgId())==6:
            newdau = newdau.daughter(0)
          if isFinal(newdau):
            dau = newdau
        
        pair.append(dau.p4())
        tree_decay.mass[0]    = moth.mass()
        tree_decay.pid[0]     = dau.pdgId()
        tree_decay.pt[0]      = dau.pt()
        tree_decay.eta[0]     = dau.eta()
        tree_decay.phi[0]     = dau.phi()
        tree_decay.isBrem[0]  = isBrem
        
        if abs(dau.pdgId())==15:
          finDaughters        = finalDaughters(dau,[ ])
          ptvis               = p4sumvis(finDaughters).pt()
          tree_decay.ptvis[0] = ptvis
          decaymode           = tauDecayMode(dau)
          tree_decay.type[0]  = decaydict[decaymode]
          #print decaymode, 'vis pt = ', ptvis , 'tau pt = ', dau.pt()
          if ptvis > dau.pt():
            print "%s, vis pt = %s, tau pt = %s "%(decaymode,ptvis,dau.pt())+'!'*30
        else:
          tree_decay.ptvis[0] = dau.pt()
          tree_decay.type[0]  = -1
        tree_decay.weight[0]  = weight
        tree_decay.Fill()
        
        if abs(moth.pdgId()) in mothids:
          hist_moth_decay.Fill(dau.pdgId())
      
      if len(pair)==2:
        tree_mother.inv[0]     = (pair[0] + pair[1]).mass()
        tree_mother.dphi_ll[0] = deltaPhi(pair[0].phi(), pair[1].phi())
        tree_mother.deta_ll[0] = pair[0].eta() - pair[1].eta()
        tree_mother.dr_ll[0]   = deltaR(pair[0].eta(),pair[0].phi(),pair[1].eta(),pair[1].phi())
      else:
        tree_mother.inv[0]     = -1
        tree_mother.dphi_ll[0] = -99
        tree_mother.deta_ll[0] = -99
        tree_mother.dr_ll[0]   = -99
      
      tree_mother.pid[0]       = moth.pdgId()
      tree_mother.moth[0]      = granma.pdgId()
      tree_mother.status[0]    = moth.status()
      tree_mother.mass[0]      = moth.mass()
      tree_mother.pt[0]        = moth.pt()
      tree_mother.eta[0]       = moth.eta()
      tree_mother.phi[0]       = moth.phi()
      tree_mother.ndau[0]      = len(pair)
      tree_mother.dau[0]       = dau_pid # save PDG ID for quark daughter
      tree_mother.weight[0]    = weight
      tree_mother.Fill()
    
    if len(gps_mother)==1:
      tree_event.moth1_mass[0]  = gps_mother[0].mass()
      tree_event.moth1_pt[0]    = gps_mother[0].pt()
      tree_event.moth2_mass[0]  = -1
      tree_event.moth2_pt[0]    = -1
    elif len(gps_mother)>=2:
      tree_event.moth1_mass[0]  = gps_mother[0].mass()
      tree_event.moth1_pt[0]    = gps_mother[0].pt()
      tree_event.moth2_mass[0]  = gps_mother[1].mass()
      tree_event.moth2_pt[0]    = gps_mother[1].pt()
    else:
      tree_event.moth1_mass[0]  = -1
      tree_event.moth1_pt[0]    = -1
      tree_event.moth2_mass[0]  = -1
      tree_event.moth2_pt[0]    = -1
    
    tree_event.ntau_assoc[0]  = len(taus_assoc)
    tree_event.ntau_decay[0]  = len(taus_decay)
    tree_event.nbgen_decay[0] = len(bgen_decay)
    tree_event.Fill()
  
  print ">>> Processed %4s events in %s"%(evtid,formatTime(time.time()-start_proc))
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

def findCentrajpt1s(leadJets, otherJets ):
  """Finds all jets between the 2 leading jets, for central jet veto."""
  if not len(otherJets):
      return []
  etamin = leadJets[0].eta()
  etamax = leadJets[1].eta()
  def isCentral(jet):
    if jet.pt()<30.:
      return False
    eta = jet.eta()
    return etamin<eta and eta<etamax
  if etamin > etamax:
      etamin, etamax = etamax, etamin
  centrajpt1s = filter(isCentral,otherJets)
  return centrajpt1s
  
def p4sumvis(particles):
  #import pdb; pdb.set_trace()
  visparticles = copy.deepcopy([p for p in particles if abs(p.pdgId()) not in [12, 14, 16]])
  p4 = visparticles[-1].p4() if particles else 0.
  visparticles.pop()
  for p in visparticles:
      p4 += p.p4()
  return p4
  
def finalDaughters(particle, daughters):
  """Fills daughters with all the daughters of particle recursively."""
  if particle.numberOfDaughters()==0:
    daughters.append(particle)
  else:
    foundDaughter = False
    for i in range( particle.numberOfDaughters() ):
      dau = particle.daughter(i)
      if dau.status()>=1:
        daughters = finalDaughters( dau, daughters )
        foundDaughter = True
    if not foundDaughter:
      daughters.append(particle)
  return daughters
  
def tauDecayMode(tau):
  unstable = True
  dm = 'tau'
  final_daughter = tau
  while unstable:
    nod = tau.numberOfDaughters()
    for i in range(nod):
      dau = tau.daughter(i)
      if abs(dau.pdgId())==11 and dau.status()==1:
        dm = 'ele'
        final_daughter = dau
        unstable = False
        break
      elif abs(dau.pdgId())==13 and dau.status()==1:
        dm = 'muon'
        final_daughter = dau
        unstable = False
        break
      elif abs(dau.pdgId())==15: #taus may do bremsstrahlung
        dm = 'tau'
        final_daughter = dau
        tau = dau # check its daughters
        break
      elif abs(dau.pdgId()) not in (12, 14, 16):
        unstable = False
        break
  return dm
  
def diTauDecayMode(decay1,decay2):
  if decay1=='ele' and decay2=='ele':
    return 5, 'ee'
  elif decay1=='muon' and decay2=='muon':
    return 3, 'mm'
  elif (decay1=='ele' and decay2=='muon') or (decay1=='muon' and decay2=='ele'):
    return 4, 'em'
  elif (decay1=='tau' and decay2=='ele') or (decay1=='ele' and decay2=='tau'):
    return 2, 'et'
  elif (decay1=='tau' and decay2=='muon') or (decay1=='muon' and decay2=='tau'):
    return 1, 'mt'
  elif decay1=='tau' and decay2=='tau':
    return 0, 'tt'
  else:
    return -1, 'anything'
  
def deltaR(eta1, phi1, eta2, phi2):
  deta = eta1 - eta2
  dphi = deltaPhi(phi1, phi2)
  return math.sqrt(deta*deta+dphi*dphi)
  
def deltaPhi(phi1, phi2):
  """Computes delta phi, handling periodic limit conditions."""
  res = phi1 - phi2
  while res > math.pi:
    res -= 2*math.pi
  while res<-math.pi:
    res += 2*math.pi
  return res
  
def cleanObjectCollection(objects, masks, dRmin):
  """Masks objects using a deltaR cut."""
  if len(objects)==0 or len(masks)==0:
    return objects, []
  cleanObjects = [ ]
  dirtyObjects = [ ]
  for object in objects:
    overlap = False
    for mask in masks:
      dR = deltaR(object.eta(),object.phi(),mask.eta(),mask.phi())
      if dR<dRmin:
        overlap = True
        break
    if overlap:
      dirtyObjects.append(object)
    else:
      cleanObjects.append(object)
  return cleanObjects, dirtyObjects
  
def isFinal(p):
  # TODO: check if one daughter is final and has same PID
  return not (p.numberOfDaughters()==1 and p.daughter(0).pdgId()==p.pdgId())
  
def isFinalM(p):
  #print p.numberOfDaughters(), p.daughter(0).pdgId(), p.pdgId(), p.status()
  #return p.numberOfDaughters()==3
  return not (p.numberOfDaughters()==3 and p.daughter(0).pdgId()==p.pdgId())
  
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
    nshow = min(len(infiles),6)
    print ">>> Input files: (showing %d/%d)"%(nshow,len(infiles))
    for file in infiles[:nshow]:
      print ">>>   %s"%(file)
  print ">>> Output file: %s"%(outfile)
  isPythia  = 'Pythia' in infiles[0]
  convertGENSIM(infiles,outfile,maxevts=maxevts,isPythia=isPythia,dtier=dtier)
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
  

