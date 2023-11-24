#! /usr/bin/env python
# Author: Izaak Neutelings (Februari, 2020)
# Description: Standalone to dump gen particle information
# Instructions: Install nanoAOD-tools and run
#   python dumpLHE.py
# Sources:
#   https://github.com/cms-nanoAOD/nanoAOD-tools#nanoaod-tools
#   https://github.com/cms-nanoAOD/nanoAOD-tools/tree/master/python/postprocessing/examples
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/examples/exampleGenDump.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/genparticles_cff.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/LHETablesProducer.cc
from __future__ import print_function # for python3 compatibility
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles', dest='infiles', action='store', type=str, default=None)
parser.add_argument('-n', '--max',     dest='maxEvts', action='store', type=int, default=20)
args = parser.parse_args()

# SETTINGS
outdir    = '.'
maxEvts   = args.maxEvts
branchsel = None

# INPUT FILES
#  dasgoclient --query="dataset=/DYJetsToLL_M-50*/*18NanoAODv5*/NANOAOD*"
#  dasgoclient --query="dataset=/DYJetsToLL_M-50_TuneCP2_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv5-PUFall18Fast_Nano1June2019_lhe_102X_upgrade2018_realistic_v19-v1/NANOAODSIM file" | head -n10
url     = "root://cms-xrd-global.cern.ch/" #"root://xrootd-cms.infn.it/"
infiles = [
  url+'/store/mc/RunIIAutumn18NanoAODv5/DYJetsToLL_M-50_TuneCP2_13TeV-madgraphMLM-pythia8/NANOAODSIM/PUFall18Fast_Nano1June2019_lhe_102X_upgrade2018_realistic_v19-v1/250000/9A3D4107-5366-C243-915A-F4426F464D2F.root',
]
if args.infiles:
  infiles = args.infiles

# HAS BIT
def hasBit(value,bit):
  """Check if i'th bit is set to 1, i.e. binary of 2^(i-1),
  from the right to the left, starting from position i=0."""
  # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
  # Gen status flags, stored bitwise, are:
  #    0: isPrompt,                          8: fromHardProcess,
  #    1: isDecayedLeptonHadron,             9: isHardProcessTauDecayProduct,
  #    2: isTauDecayProduct,                10: isDirectHardProcessTauDecayProduct,
  #    3: isPromptTauDecayProduct,          11: fromHardProcessBeforeFSR,
  #    4: isDirectTauDecayProduct,          12: isFirstCopy,
  #    5: isDirectPromptTauDecayProduct,    13: isLastCopy,
  #    6: isDirectHadronDecayProduct,       14: isLastCopyBeforeFSR
  #    7: isHardProcess,
  ###return bin(value)[-bit-1]=='1'
  ###return format(value,'b').zfill(bit+1)[-bit-1]=='1'
  return (value & (1 << bit))>0

# DUMPER MODULE
class LHEDumper(Module):
  
  def __init__(self):
    self.nleptons = 0
    self.nevents  = 0
  
  def analyze(self,event):
    """Dump gen information for each gen particle in given event."""
    print("\n%s event %s %s"%('-'*10,event.event,'-'*60))
    self.nevents += 1
    leptonic = False
    particles = Collection(event,'GenPart')
    #particles = Collection(event,'LHEPart')
    print(" \033[4m%7s %8s %8s %8s %8s %8s %8s %8s %9s %10s  \033[0m"%(
      "index","pdgId","moth","mothid","dR","pt","eta","status","prompt","last copy"))
    for i, particle in enumerate(particles):
      mothidx  = particle.genPartIdxMother
      if 0<=mothidx<len(particles):
        moth    = particles[mothidx]
        mothpid = moth.pdgId
        mothdR  = min(999,particle.DeltaR(moth)) #particle.p4().DeltaR(moth.p4())
      else:
        mothpid = -1
        mothdR  = -1
      eta       = min(999,particle.eta)
      prompt    = hasbit(particle.statusFlags,0)
      lastcopy  = hasbit(particle.statusFlags,13)
      print(" %7d %8d %8d %8d %8.2f %8.2f %8.2f %8d %9s %10s"%(
        i,particle.pdgId,mothidx,mothpid,mothdR,particle.pt,eta,particle.status,prompt,lastcopy))
      if abs(particle.pdgId) in [11,13,15]:
        leptonic = True
    if leptonic:
      self.nleptons += 1
  
  def endJob(self):
    print('\n'+'-'*80)
    if self.nevents>0:
      print("  %-10s %4d / %-4d (%.1f%%)"%('leptonic:',self.nleptons,self.nevents,100.0*self.nleptons/self.nevents))
    print("%s done %s\n"%('-'*10,'-'*64))
  
# PROCESS NANOAOD
processor = PostProcessor(outdir,infiles,noOut=True,modules=[LHEDumper()],maxEntries=maxEvts)
processor.run()
