#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2020)
# Description:
#   Simple example of gen-level study of dilepton events.
# Instructions to run standalone:
#   python3 python/analysis/gmin2/ModuleGen_gmin2.py -s m -t _mumu -n 100000
#   python3 python/analysis/gmin2/ModuleGen_gmin2.py -s t -t _tautau -n 100000
# Instructions to run with pico.py:
#   pico.py channel gen python/analysis/gmin2/ModuleGen_gmin2.py
#   pico.py era UL2018 samples/gmin2/samples_UL2018.py
#   pico.py run -c gen -y 2018 -s GGToMuMu -m 10000 -n10
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


def addcopies(part,genparts):
  """Return list of particles in productions chain."""
  copies = [part] # list of all copies given particle
  moth   = None # GenPart object of mother
  imoth  = part.genPartIdxMother # index of mother in GenPart collection
  while imoth>=0:
    moth = genparts[imoth]
    imoth = moth.genPartIdxMother
    if moth.pdgId==part.pdgId:
      copies.insert(0,moth) # reverse order (first to last copy)
    else: # break at first mother of different PDG ID
      break
  part.mothid = 0 if moth==None else moth.pdgId
  part.copies = copies
  return moth, copies
  
def mapabspid(pid):
  """Map absolute value of lepton PDG ID to bin number."""
  if   pid==0:  return 0
  elif pid==11: return 1
  elif pid==13: return 2
  elif pid==15: return 3
  print(f">>> mapsabspid: WARNING! Unrecognized PID={pid}")
  return -1
  
def mappid(pid):
  """Map absolute value of lepton PDG ID to bin number."""
  if   pid==0:   return 0
  elif pid==11:  return 1
  elif pid==-11: return 2
  elif pid==13:  return 3
  elif pid==-13: return 4
  elif pid==15:  return 5
  elif pid==-15: return 6
  print(f">>> mappid: WARNING! Unrecognized PID={pid}")
  return -1
  
def mappid2(pid1,pid2):
  """Map absolute value of lepton PDG ID to bin number."""
  if pid1==-pid2:
    if       pid1==0:   return 0
    elif abs(pid1)==11: return 2
    elif abs(pid1)==13: return 3
    elif abs(pid1)==15: return 4
  elif pid1==0 or pid2==0:
    return 1
  return 5
  

# MAIN PHYSICAL ANALYSIS MODULE
class ModuleGen_gmin2(Module):
  """Find interesting particles for gen studies of dilepton production."""
  
  def __init__(self,fname,**kwargs):
    
    # CREATE OUTPUT FILE with single tree
    self.out = TreeProducer(fname,self,**kwargs)
    self.branchsel = branchsel # disable unneeded branches for faster processing
    
    # ADD CUTS TO CUTFLOW
    self.out.cutflow.addcut('nocut', "No cut")
    self.out.cutflow.addcut('lep',   "1 lepton")
    self.out.cutflow.addcut('pair',  "2 leptons")
    self.out.cutflow.addcut('charge',"Opposite charge")
    
    # ADD HISTOGRAMS
    abspidlabs = ["None","e","#mu","#tau"] # axis labels for leptons PDG
    pidlabs    = ["None","e^{+}","e^{#minus}","#mu^{+}","#mu^{#minus}","#tau^{+}","#tau^{#minus}"] # axis labels for leptons PDG
    pidlabs2   = ["No lep","1 lep","e^{+}e^{#minus}","#mu^{+}#mu^{#minus}","#tau^{+}#tau^{#minus}","Other"] # axis labels for leptons PDG
    self.out.addHist('nfsr',      "Number of FSR photons of two leading lepton",10,0,10) # to study FSR
    #self.out.addHist('nfsr_pos',  "Number of FSR photons of positively charged lepton",10,0,10) # to study FSR
    #self.out.addHist('nfsr_neg',  "Number of FSR photons of negatively charged lepton",10,0,10) # to study FSR
    #self.out.addHist('nfsr_os',   "Number of FSR photons of OS leptons;Number of FSR photons of positively charged lepton;Number of FSR photons of negatively charged lepton",
    #  10,0,10,10,0,10) # to study FSR
    self.out.addHist('nfsr2D',    "Number of FSR photons of two leading lepton;Number of FSR photons from leading lepton;Number of FSR photons from subleading lepton",
                     10,0,10,10,0,10,option='COLZ TEXT44') # to study FSR
    self.out.addHist('dphi_fsr',  "#Delta#eta between lepton before and after FSR",       100,0,4) # to study FSR
    self.out.addHist('dphi_fsr1', "#Delta#eta between lepton before and after single FSR",100,0,4) # to study FSR
    self.out.addHist('deta_fsr',  "#Delta#eta between lepton before and after FSR",       100,0,5) # to study FSR
    self.out.addHist('deta_fsr1', "#Delta#eta between lepton before and after single FSR",100,0,5) # to study FSR
    self.out.addHist('dR_fsr',    "#DeltaR between lepton before and after FSR",          100,0,5) # to study FSR
    self.out.addHist('dR_fsr1',   "#DeltaR between lepton before and after single FSR",   100,0,5) # to study FSR
    self.out.addHist('dpt_fsr',   "(p_{T}^{after}-p_{T}^{before})/p_{T}^{before} between lepton before and after FSR",       100,-1.4,0.7) # to study FSR
    self.out.addHist('dpt_fsr1',  "(p_{T}^{after}-p_{T}^{before})/p_{T}^{before} between lepton before and after single FSR",100,-1.4,0.7) # to study FSR
    self.out.addHist('dphi_deta_fsr', "Before and after FSR;#Delta#eta;#Delta#phi",       100,0,4,100,0,4) # to study FSR
    self.out.addHist('dphi_deta_fsr1',"Before and after single FSR;#Delta#eta;#Delta#phi",100,0,4,100,0,4) # to study FSR
    self.out.addHist('pt_pt_fsr',     "Lepton pT before and after FSR;Lepton p_{T} before FSR [GeV];Lepton pT after FSR [GeV];",       40,0,120,40,0,120) # to study FSR
    self.out.addHist('pt_pt_fsr1',    "Lepton pT before and after single FSR;Lepton p_{T} before FSR [GeV];Lepton pT after FSR [GeV];",40,0,120,40,0,120) # to study FSR
    self.out.addHist('dpt_dR_fsr',    "Before and after FSR;#DeltaR;(p_{T}^{after}-p_{T}^{before})/p_{T}^{before}",       100,-1.4,0.7,100,0,5) # to study FSR
    self.out.addHist('dpt_dR_fsr1',   "Before and after single FSR;#DeltaR;(p_{T}^{after}-p_{T}^{before})/p_{T}^{before}",100,-1.4,0.7,100,0,5) # to study FSR
    self.out.addHist('dpt_pt_fsr',    "Lepton pT before and after FSR;Lepton p_{T} before FSR [GeV];(p_{T}^{after}-p_{T}^{before})/p_{T}^{before};",       40,0,120,100,-1.4,0.7) # to study FSR
    self.out.addHist('dpt_pt_fsr1',   "Lepton pT before and after single FSR;Lepton p_{T} before FSR [GeV];(p_{T}^{after}-p_{T}^{before})/p_{T}^{before};",40,0,120,100,-1.4,0.7) # to study FSR
    self.out.addHist('ncopies',     "Number of copies of two leading lepton",10,0,10) # to study FSR
    self.out.addHist('pid_lep1D',   "Final state of two leading leptons",6,0,6,xlabs=pidlabs2,lsize=0.045)
    self.out.addHist('abspid_lep2D',"Final state of two leading leptons;Leading lepton;Subleading lepton",4,0,4,4,0,4,
                     xlabs=abspidlabs,ylabs=abspidlabs,lsize=0.045,option='COLZ TEXT44')
    self.out.addHist('pid_lep2D',"Final state of two leading leptons;Leading lepton;Subleading lepton",7,0,7,7,0,7,
                     xlabs=pidlabs,ylabs=pidlabs,lsize=0.045,option='COLZ TEXT44')
    ###self.out.addHist('pt_pos',"pT of positively charged lepton",100,0,300)
    ###self.out.addHist('pt_neg',"pT of negatively charged lepton",100,0,300)
    ###self.out.addHist('pt_os',"pT of OS-charge leptons;pT of positively charged lepton;pT of negatively charged lepton",100,0,300,100,0,300)
    
    # ADD BRANCHES for EVENT
    self.out.addBranch('genweight',      'f', title="Generator weight")
    self.out.addBranch('nelecs',         'i', title="Number of electrons")
    self.out.addBranch('nmuons',         'i', title="Number of muons")
    self.out.addBranch('ntaus',          'i', title="Number of tau leptons")
    self.out.addBranch('nfsr',           'i', title="Number of FSR photons (from two leading leptons)")
    self.out.addBranch('nfsr1',          'i', title="Number of FSR photons with pT > 1 GeV (from two leading leptons)")
    self.out.addBranch('nfsr10',         'i', title="Number of FSR photons with pT > 10 GeV (from two leading leptons)")
    
    # ADD BRANCHES for LEPTONS
    self.out.addBranch('pt_lep1',        'f', title="pT of leading lepton")
    self.out.addBranch('pt_lep2',        'f', title="pT of subleading lepton")
    self.out.addBranch('ptfirst_lep1',   'f', title="pT of first copy of leading lepton")
    self.out.addBranch('ptfirst_lep2',   'f', title="pT of first copy of subleading lepton")
    self.out.addBranch('eta_lep1',       'f', title="eta of leading lepton")
    self.out.addBranch('eta_lep2',       'f', title="eta of subleading lepton")
    self.out.addBranch('etafirst_lep1',  'f', title="eta of first copy leading lepton")
    self.out.addBranch('etafirst_lep2',  'f', title="eta of first copy subleading lepton")
    self.out.addBranch('phi_lep1',       'f', title="phi of leading lepton")
    self.out.addBranch('phi_lep2',       'f', title="phi of subleading lepton")
    self.out.addBranch('phifirst_lep1',  'f', title="phi of first copy leading lepton")
    self.out.addBranch('phifirst_lep2',  'f', title="phi of first copy subleading lepton")
    self.out.addBranch('pid_lep1',       'i', title="PDG ID of leading lepton")
    self.out.addBranch('pid_lep2',       'i', title="PDG ID of subleading lepton")
    self.out.addBranch('moth_lep1',      'i', title="PDG ID of mother of leading lepton")
    self.out.addBranch('moth_lep2',      'i', title="PDG ID of mother of subleading lepton")
    self.out.addBranch('flags_lep1',     'i', title="Status flags of leading lepton")
    self.out.addBranch('flags_lep2',     'i', title="Status flags of subleading lepton")
    self.out.addBranch('status_lep1',    'i', title="Status of leading lepton")
    self.out.addBranch('status_lep2',    'i', title="Status of subleading lepton")
    self.out.addBranch('nphotons_lep1',  'i', title="Number of photons of leading lepton")
    self.out.addBranch('nphotons_lep2',  'i', title="Number of photons of subleading lepton")
    
    # ADD BRANCHES for LEPTON PAIRS
    self.out.addBranch('dR_ll',          'f', title="dR between two leading leptons")
    self.out.addBranch('dphi_ll',        'f', title="dphi between two leading leptons")
    
    # ADD ALIASES (to save disk space)
    self.out.setAlias('nleptons', "nelecs+nmuons+ntaus")
    #self.out.setAlias('nfsr',     "nphotons_lep1+nphotons_lep2")
    self.out.setAlias('aco',      "(1-abs(dphi_ll)/3.14159265)") # acoplanarity
    #self.out.setAlias('dphi_vistau', "ROOT::VecOps::DeltaPhi(phi_vistau1,phi_vistau2)") # fold with ROOT::VecOps::DeltaPhi
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    hist = self.out.hists['pid_lep1D']
    nall = hist.GetEntries()
    if nall>0:
      print(">>> Two leading leptons:")
      for i in range(1,hist.GetXaxis().GetNbins()+1):
        nevt = int(hist.GetBinContent(i))
        name = hist.GetXaxis().GetBinLabel(i).replace('#','').replace('^{+}','+').replace('^{minus}','-')
        eff  = nevt/nall # efficiency
        err  = sqrt(eff*(1.-eff)/nall) # uncertainty in efficiency
        seff = f"{0:4d}" if nevt==0 else f"({100*eff:6.2f} +-{100*err:5.2f} )"
        print(f">>>   {name:<8s} {nevt:7d} / {nall} = {seff}%")
    self.out.endJob()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('nocut')
    
    # PREPARE lists of selected gen-level particles
    elecs   = [ ] # electrons
    muons   = [ ] # muons
    taus    = [ ] # tau leptons (before decay)
    photons = [ ] # photons from leptons
    
    # LOOP over gen-level particles
    #print('-'*80) # print to separate events during debugging
    genparts  = Collection(event,'GenPart') # generator-level particles
    for part in genparts:
      #dumpgenpart(part,genparts,flags=['isFirstCopy','isLastCopy','isTauDecayProduct']) # print for debugging
      pid = abs(part.pdgId) # remove charge sign
      #if pid not in [11,13,15,22]:
      #  continue # only analyze leptons and photons
      if not part.statusflag('isLastCopy'):
        continue # only analyze last copies
      
      # ELECTRON
      elif pid==11:
        elecs.append(part)
        part.photons = [ ]
        addcopies(part,genparts)
      
      # MUON
      elif pid==13:
        muons.append(part)
        part.photons = [ ]
        addcopies(part,genparts)
        #print(f">>> {part}, mother={part.mothid}, ncopies={len(part.copies)}")
        #print(">>> "+getprodchain(part,genparts))
        #dumpgenpart(part,genparts,flags=['isFirstCopy','isLastCopy','isTauDecayProduct']) # print for debugging
      
      # TAU lepton
      elif pid==15:
        taus.append(part)
        part.photons = [ ]
        addcopies(part,genparts)
      
      # PHOTONS (FSR from tau)
      elif pid==22:
        mother = getmother(part,genparts) # get mother
        if abs(mother.pdgId) in [11,13,15]: # FSR from lepton
          part.mother = mother
          photons.append(part) # save for counting FSR later
          #print(getprodchain(part,genparts))
          #dumpgenpart(part,genparts,flags=['isTauDecayProduct','isPromptTauDecayProduct','isDirectTauDecayProduct','isDirectHadronDecayProduct']) # print for debugging
    
    # MATCH FSR PHOTONS with last copy of mother leptons
    for photon in photons:
      lastlep = getlastcopy(photon.mother,genparts) # get last copy of tau (after all FSR)
      lastlep.photons.append(photon)
    
    # SANITY CHECKS for charge balance
    leptons = elecs+muons+taus
    for lepton in leptons:
      if len(lepton.photons)>=1:
        lepton0 = lepton.copies[0]
        assert lepton!=lepton0
        dphi = deltaPhi(lepton0.phi,lepton.phi)
        deta = abs(lepton0.eta-lepton.eta)
        dR   = sqrt(dphi*dphi+deta*deta)
        dpt  = (lepton.pt-lepton0.pt)/lepton0.pt if lepton0.pt>0 else 0
        self.out.fill('dphi_fsr',     dphi)
        self.out.fill('deta_fsr',     deta)
        self.out.fill('dR_fsr',       dR)
        self.out.fill('dpt_fsr',      dpt)
        self.out.fill('dphi_deta_fsr',deta,dphi)
        self.out.fill('pt_pt_fsr',    lepton0.pt,lepton.pt)
        self.out.fill('dpt_dR_fsr',   dR,dpt)
        self.out.fill('dpt_pt_fsr',   lepton0.pt,dpt)
        if len(lepton.photons)==1: # single FSR for this lepton
          self.out.fill('dphi_fsr1',     dphi)
          self.out.fill('deta_fsr1',     deta)
          self.out.fill('dR_fsr1',       dR)
          self.out.fill('dpt_fsr1',      dpt)
          self.out.fill('dphi_deta_fsr1',deta,dphi)
          self.out.fill('pt_pt_fsr1',    lepton0.pt,lepton.pt)
          self.out.fill('dpt_dR_fsr1',   dR,dpt)
          self.out.fill('dpt_pt_fsr1',   lepton0.pt,dpt)
      ###if lepton.pdgId>0: # positive charge
      ###  self.out.fill('pt_pos',lepton.pt)
      ###  self.out.fill('nfsr_pos',len(lepton.photons))
      ###else: # negatively charged
      ###  self.out.fill('pt_neg',lepton.pt)
      ###  self.out.fill('nfsr_neg',len(lepton.photons))
      ###poslep = [l for l in leptons if l.pdgId>0]
      ###neglep = [l for l in leptons if l.pdgId<0]
      ###if len(poslep)>=1 and len(neglep)>=1:
      ###  self.out.fill('pt_os',poslep[0].pt,neglep[0].pt)
      ###  self.out.fill('nfsr_os',len(poslep[0].photons),len(neglep[0].photons))
    
    # SORT LEPTONS BY PT
    leptons = elecs+muons+taus
    leptons.sort(key=lambda l: l.pt,reverse=True) # sort leptons by pT
    leptons = leptons[:2] # only store two leading ones
    
    # FILL BRANCHES
    self.out.genweight[0] = event.genWeight
    self.out.nelecs[0]    = len(elecs)
    self.out.nmuons[0]    = len(muons)
    self.out.ntaus[0]     = len(taus)
    self.out.nfsr[0]      = sum(len(l.photons) for l in leptons[:2])
    self.out.nfsr1[0]     = sum(sum(p.pt>1 for p in l.photons) for l in leptons[:2])
    self.out.nfsr10[0]    = sum(sum(p.pt>10 for p in l.photons) for l in leptons[:2])
    
    # FILL TAU BRANCHES
    if len(leptons)>=2:
      self.out.fill('nfsr2D',len(leptons[0].photons),len(leptons[1].photons)) # number of FSR photons
      p4_lep1 = leptons[0].p4()
      p4_lep2 = leptons[1].p4()
      self.out.dR_ll[0]         = p4_lep1.DeltaR(p4_lep2)
      self.out.dphi_ll[0]       = p4_lep1.DeltaPhi(p4_lep2)
      self.out.pt_lep1[0]       = leptons[0].pt
      self.out.pt_lep2[0]       = leptons[1].pt
      self.out.ptfirst_lep1[0]  = leptons[0].copies[0].pt
      self.out.ptfirst_lep2[0]  = leptons[1].copies[0].pt
      self.out.eta_lep1[0]      = leptons[0].eta
      self.out.eta_lep2[0]      = leptons[1].eta
      self.out.etafirst_lep1[0] = leptons[0].copies[0].eta
      self.out.etafirst_lep2[0] = leptons[1].copies[0].eta
      self.out.phi_lep1[0]      = leptons[0].phi
      self.out.phi_lep2[0]      = leptons[1].phi
      self.out.phifirst_lep1[0] = leptons[0].copies[0].phi
      self.out.phifirst_lep2[0] = leptons[1].copies[0].phi
      self.out.moth_lep1[0]     = leptons[0].mothid
      self.out.moth_lep2[0]     = leptons[1].mothid
      self.out.pid_lep1[0]      = leptons[0].pdgId
      self.out.pid_lep2[0]      = leptons[1].pdgId
      self.out.status_lep1[0]   = leptons[0].status
      self.out.status_lep2[0]   = leptons[1].status
      self.out.flags_lep1[0]    = leptons[0].statusFlags
      self.out.flags_lep2[0]    = leptons[1].statusFlags
      self.out.nphotons_lep1[0] = len(leptons[0].photons)
      self.out.nphotons_lep2[0] = len(leptons[1].photons)
    elif len(leptons)>=1:
      self.out.dR_ll[0]         = -1
      self.out.dphi_ll[0]       = -9
      self.out.pt_lep1[0]       = leptons[0].pt
      self.out.pt_lep2[0]       = -1
      self.out.ptfirst_lep1[0]  = leptons[0].copies[0].pt
      self.out.ptfirst_lep2[0]  = -1
      self.out.eta_lep1[0]      = leptons[0].eta
      self.out.eta_lep2[0]      = -9
      self.out.etafirst_lep1[0] = leptons[0].copies[0].eta
      self.out.etafirst_lep2[0] = -9
      self.out.phi_lep1[0]      = leptons[0].phi
      self.out.phi_lep2[0]      = -9
      self.out.phifirst_lep1[0] = leptons[0].copies[0].phi
      self.out.phifirst_lep2[0] = -9
      self.out.moth_lep1[0]     = leptons[0].mothid
      self.out.moth_lep2[0]     = 0
      self.out.pid_lep1[0]      = leptons[0].pdgId
      self.out.pid_lep2[0]      = 0
      self.out.status_lep1[0]   = leptons[0].status
      self.out.status_lep2[0]   = -1
      self.out.flags_lep1[0]    = leptons[0].statusFlags
      self.out.flags_lep2[0]    = -1
      self.out.nphotons_lep1[0] = len(leptons[0].photons)
      self.out.nphotons_lep2[0] = -1
    else: # no leptons found
      self.out.dR_ll[0]         = -1
      self.out.dphi_ll[0]       = -9
      self.out.pt_lep1[0]       = -1
      self.out.pt_lep2[0]       = -1
      self.out.ptfirst_lep1[0]  = -1
      self.out.ptfirst_lep2[0]  = -1
      self.out.eta_lep1[0]      = -9
      self.out.eta_lep2[0]      = -9
      self.out.etafirst_lep1[0] = -9
      self.out.etafirst_lep2[0] = -9
      self.out.phi_lep1[0]      = -9
      self.out.phi_lep2[0]      = -9
      self.out.phifirst_lep1[0] = -9
      self.out.phifirst_lep2[0] = -9
      self.out.moth_lep1[0]     = 0
      self.out.moth_lep2[0]     = 0
      self.out.pid_lep1[0]      = 0
      self.out.pid_lep2[0]      = 0
      self.out.status_lep1[0]   = -1
      self.out.status_lep2[0]   = -1
      self.out.flags_lep1[0]    = -1
      self.out.flags_lep2[0]    = -1
      self.out.nphotons_lep1[0] = -1
      self.out.nphotons_lep2[0] = -1
    
    # FILL CUTFLOW
    if len(leptons)>=1:
      self.out.cutflow.fill('lep')
      if len(leptons)>=2:
        self.out.cutflow.fill('pair')
        if leptons[0].pdgId*leptons[1].pdgId<0:
          self.out.cutflow.fill('charge')
        ###else: # debugging
        ###  print(f">>> WARNING! Two Leading leptons are same-sign!")
        ###  dumpgenpart(leptons[0],genparts,flags=['isFirstCopy','isLastCopy','isTauDecayProduct']) # print for debugging
        ###  dumpgenpart(leptons[1],genparts,flags=['isFirstCopy','isLastCopy','isTauDecayProduct']) # print for debugging
        ###  print(">>>  "+getprodchain(leptons[0],genparts))
        ###  print(">>>  "+getprodchain(leptons[1],genparts))
    
    # FILL HISTOGRAMS
    for lepton in leptons:
      self.out.fill('nfsr',len(lepton.photons))  # number of FSR photons
      self.out.fill('ncopies',len(lepton.copies)) # number of copies
    self.out.fill('pid_lep1D',mappid2(self.out.pid_lep1[0],self.out.pid_lep2[0]))
    self.out.fill('abspid_lep2D',
      mapabspid(abs(self.out.pid_lep1[0])),mapabspid(abs(self.out.pid_lep2[0])))
    self.out.fill('pid_lep2D',
      mappid(self.out.pid_lep1[0]),mappid(self.out.pid_lep2[0]))
    
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
  parser.add_argument('-s',   '--sample', choices=['m','t'], default='m',
                                          help="select pre-defined list of input files")
  args = parser.parse_args()
  
  # SETTINGS
  maxevts   = args.maxevts if args.maxevts>0 else None
  outfname  = "genAnalyzer_gmin2%s.root"%(args.tag)
  modules   = [ModuleGen_gmin2(outfname)]
  
  # INPUT FILES
  url = "root://cms-xrd-global.cern.ch/"
  indir = "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD"
  if args.infiles:
    infiles = args.infiles
  elif args.sample=='m': # GGToMuMu
    infiles = [
      indir+"/GGToMuMu_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122720/0000/NanoAODv9_1.root",
      indir+"/GGToMuMu_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122720/0000/NanoAODv9_2.root",
      indir+"/GGToMuMu_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122720/0000/NanoAODv9_3.root",
    ]
  elif args.sample=='t': # GGToTauTau
    infiles = [
      indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_1.root",
      indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_2.root",
      indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_3.root",
      indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_4.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_5.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_6.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_7.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_8.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_9.root",
      #indir+"/GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000/NanoAODv9_10.root",
    ]
  
  # PROCESS NANOAOD
  processor = PostProcessor(args.outdir,infiles,modules=modules,maxEntries=maxevts,
                            branchsel=branchsel,noOut=True)
  processor.run()
  
