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
from ROOT import TFile, TH1F, TTree, gStyle, TH2F
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
  assert events.size()>0, "Number of entries in Events tree = %s <= 0"%(events.size())
  outfile = TFile(outfilename,'RECREATE')
  
  # PREPARE TREE
  print ">>> Creating output trees and branches..."
  tree  = TTree('event', 'event')
  tree.addBranch('nmoth',       'i')
  tree.addBranch('nmuon',       'i')
  tree.addBranch('ntau',        'i')
  tree.addBranch('ntau_hard',   'i')
  tree.addBranch('ntauh',       'i')
  tree.addBranch('moth_m',      'f')
  tree.addBranch('moth_pt',     'f')
  tree.addBranch('moth_pid',    'i')
  tree.addBranch('moth_status', 'i')
  tree.addBranch('tau1_pt',     'f')
  tree.addBranch('tau1_eta',    'f')
  tree.addBranch('tau2_pt',     'f')
  tree.addBranch('tau2_eta',    'f')
  tree.addBranch('muon_q',      'f')
  tree.addBranch('tauh_q',      'f')
  tree.addBranch('weight',      'f')
  
  if 'AOD' in dtier:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'prunedGenParticles'
    handle_weight, label_weight = Handle('GenEventInfoProduct'), 'generator'
  else:
    handle_gps,    label_gps    = Handle('std::vector<reco::GenParticle>'), 'genParticles'
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
    event.getByLabel(label_weight,handle_weight) # gen weight
    
    # GEN PARTICLES
    gps_final  = [p for p in gps if isFinal(p) and abs(p.pdgId()) in [5,6,11,12,13,14,15,16]+mothids] #isLastCopy()
    gps_mother = [p for p in gps_final if abs(p.pdgId()) in mothids and p.status()>60]
    if not gps_mother:
      continue # only look at events with Z bosons
    moth = gps_mother[-1] # take last one
    
    # TAUS
    gps_tau = [p for p in gps_final if abs(p.pdgId())==15 and p.status()==2]
    gps_tau_hard = [p for p in gps_tau if p.mother(0)==moth]
    if len(gps_tau_hard)<2:
      continue # only look at events with Z -> tautau
    gps_muons = [p for p in gps_final if abs(p.pdgId())==13]
    if len(gps_muons)<1:
      continue # only look at events with Z -> tautau -> mutau
    
    # CHECK FOR MUTAU
    muon_tau = None
    tauh_tau = None
    skip     = False
    for tau in gps_tau_hard:
      for i in range(moth.numberOfDaughters()):
        dau = tau.daughter(i)
        assert abs(dau.pdgId())!=15 # should already be final
        ###while abs(dau.pdgId())==15: # unlikely
        ###  dau = dau.daughter(0)
        if abs(dau.pdgId())==13: # muonic decay
          if muon_tau: skip = True; break # require only one muon
          muon_tau = dau
          break # check next tau
        elif abs(dau.pdgId())>20: # non-leptonic decay
          if tauh_tau: skip = True; break # require only one tauh
          tauh_tau = tau
          break # check next tau
      else: # no break: did not find muon or non-leptonic decay
        skip = True; break
      if skip:
        break
    if skip or not muon_tau or not tauh_tau: # failed mutau requirement
      continue
    
    gweight             = handle_weight.product()
    tree.weight[0]      = gweight.weight()
    tree.nmoth[0]       = len(gps_mother)
    tree.moth_pid[0]    = moth.pdgId()
    tree.moth_status[0] = moth.status()
    tree.moth_m[0]      = moth.mass()
    tree.moth_pt[0]     = moth.pt()
    
    # MULTIPLICITIES
    gps_tau.sort(key=lambda p: p.pt(),reverse=True)
    tree.nmuon[0]     = len(gps_muons)
    tree.ntau[0]      = len(gps_tau)
    tree.ntau_hard[0] = len(gps_tau_hard)
    tree.tau1_pt[0]   = gps_tau[0].pt()
    tree.tau1_eta[0]  = gps_tau[0].eta()
    tree.tau2_pt[0]   = gps_tau[1].pt()
    tree.tau2_eta[0]  = gps_tau[1].eta()
    tree.muon_q[0]    = -muon_tau.pdgId()/13
    tree.tauh_q[0]    = -tauh_tau.pdgId()/15
    
    tree.Fill()
  
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
  

def isFinal(p):
  return not (p.numberOfDaughters()==1 and p.daughter(0).pdgId()==p.pdgId())
  

def printParticle(p):
  string = "%9d: status=%2d, pt=%7.2f, eta=%5.2f, phi=%5.2f, final=%5s"%(p.pdgId(),p.status(),p.pt(),p.eta(),p.phi(),isFinal(p))
  if p.numberOfMothers()>=2:
    string += ", mothers %s, %s"%(p.mother(0).pdgId(),p.mother(1).pdgId())
  elif p.numberOfMothers()==1:
    string += ", mother %s"%(p.mother(0).pdgId())
  if p.numberOfDaughters()>=2:
    string += ", daughters %s, %s"%(p.daughter(0).pdgId(),p.daughter(1).pdgId())
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
  

