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


#def hasbit(value,bit):
#  https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
#  """Check if i'th bit is set to 1, i.e. binary of 2^i,
#  from the right to the left, starting from position i=0."""
#  return (value & (1 << bit))>0


def parsechain(particles,seeds,chain,indent=""):
  """Recursively print decay chain from dictionary."""
  string = ""
  for i, seed in enumerate(seeds):
    if indent=="": # beginning of chain
      substr = "%3d(%d,%d)"%(particles[seed].pdgId,seed,particles[seed].status)
    else:
      substr = " -> %3d(%d,%d)"%(particles[seed].pdgId,seed,particles[seed].status)
    if len(chain[seed])>0:
      subind  = indent+' '*len(substr)
      substr += parsechain(particles,chain[seed],chain,subind)
    string += substr
    if i<len(seeds)-1:
      string += '\n'+indent
  return string
  

# DUMPER MODULE
class GenDumper(Module):
  
  def __init__(self,*args,**kwargs):
    self.nleptons = 0
    self.nevents  = 0
    self.seedpids = [23] # print decay chain of particles with these PIDs
  
  def analyze(self,event):
    """Dump gen information for each gen particle in given event."""
    print "\n%s event %s %s"%('-'*10,event.event,'-'*68)
    self.nevents += 1
    leptonic  = False
    particles = Collection(event,'GenPart')
    #particles = Collection(event,'LHEPart')
    seeds     = [ ] # seeds for decay chain
    chain     = { } # decay chain
    print " \033[4m%7s %8s %8s %8s %8s %8s %8s %8s %9s %10s  \033[0m"%(
      "index","pdgId","moth","mothid","dR","pt","eta","status","prompt","last copy")
    for i, particle in enumerate(particles):
      mothidx  = particle.genPartIdxMother
      if 0<=mothidx<len(particles):
        moth    = particles[mothidx]
        mothpid = moth.pdgId
        mothdR  = min(9999,particle.DeltaR(moth)) #particle.p4().DeltaR(moth.p4())
      else:
        mothpid = -1
        mothdR  = -1
      eta       = max(-9999,min(9999,particle.eta))
      prompt    = particle.statusflag('isPrompt') #hasbit(particle.statusFlags,0)
      lastcopy  = particle.statusflag('isLastCopy') #hasbit(particle.statusFlags,13)
      #bothflags = (particle.statusFlags & 8193)==8193 # test both bits simultaneously: 2^0 + 2^13 = 8193
      #assert (prompt and lastcopy)==bothflags
      print " %7d %8d %8d %8d %8.2f %8.2f %8.2f %8d %9s %10s"%(
        i,particle.pdgId,mothidx,mothpid,mothdR,particle.pt,eta,particle.status,prompt,lastcopy)#,bothflags
      if abs(particle.pdgId) in [11,13,15]:
        leptonic = True
      if mothidx in chain: # add to decay chain
        chain[mothidx].append(i)
        chain[i] = [ ] # daughters
      elif abs(particle.pdgId) in self.seedpids: # save as decay chain seed
        seeds.append(i)
        chain[i] = [ ] # daughters
    if leptonic:
      self.nleptons += 1
    print parsechain(particles,seeds,chain) # print decay chain
  
  def endJob(self):
    print '\n'+'-'*80
    if self.nevents>0:
      print "  %-10s %4d / %-4d (%.1f%%)"%('leptonic:',self.nleptons,self.nevents,100.0*self.nleptons/self.nevents)
    print "%s done %s\n"%('-'*10,'-'*64)
  
