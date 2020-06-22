# Author: Izaak Neutelings (June 2020)
# Description: Dump gen particle information
# Sources:
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/processors/dumpGen.py
#   https://github.com/cms-nanoAOD/nanoAOD-tools#nanoaod-tools
#   https://github.com/cms-nanoAOD/nanoAOD-tools/tree/master/python/postprocessing/examples
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/genparticles_cff.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/LHETablesProducer.cc
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.analysis.utils import hasbit

# DUMPER MODULE
class GenDumper(Module):
  
  def __init__(self,*args,**kwargs):
    self.nleptons = 0
    self.nevents  = 0
  
  def analyze(self,event):
    """Dump gen information for each gen particle in given event."""
    print "\n%s event %s %s"%('-'*10,event.event,'-'*60)
    self.nevents += 1
    leptonic = False
    particles = Collection(event,'GenPart')
    #particles = Collection(event,'LHEPart')
    print " \033[4m%7s %8s %8s %8s %8s %8s %8s %8s %9s %10s  \033[0m"%(
      "index","pdgId","moth","mothid","dR","pt","eta","status","prompt","last copy")
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
      print " %7d %8d %8d %8d %8.2f %8.2f %8.2f %8d %9s %10s"%(
        i,particle.pdgId,mothidx,mothpid,mothdR,particle.pt,eta,particle.status,prompt,lastcopy)
      if abs(particle.pdgId) in [11,13,15]:
        leptonic = True
    if leptonic:
      self.nleptons += 1
  
  def endJob(self):
    print '\n'+'-'*80
    if self.nevents>0:
      print "  %-10s %4d / %-4d (%.1f%%)"%('leptonic:',self.nleptons,self.nevents,100.0*self.nleptons/self.nevents)
    print "%s done %s\n"%('-'*10,'-'*64)
  
