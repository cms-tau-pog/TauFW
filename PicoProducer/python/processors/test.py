#! /usr/bin/env python
# Author: Izaak Neutelings (April 2020)
# Description: Speed test of nanoAOD postprocessing
import os, sys
import time; time0 = time.time()
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles', dest='infiles', type=str, default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',  dest='outdir',  type=str, default='.')
parser.add_argument('-m', '--maxevts', dest='maxevts', type=int, default=100)
parser.add_argument('-t', '--tag',     dest='tag',     type=str, default="")
args = parser.parse_args()


##############
#   MODULE   #
##############

class TestModule(Module):
    
    def __init__(self):
        pass
        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        """Create branches in output tree."""
        self.out = wrappedOutputTree
        self.out.branch('pt_1',  'F')
        self.out.branch('eta_1', 'F')
        self.out.branch('iso_1', 'F')
        
    def beginJob(self):
        self.time0 = time.time()
        
    def endJob(self):
        print ">>> endJob: done after %.1f seconds"%(time.time()-self.time0)
        
    def analyze(self, event):
        """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
        
        ## WITH ARRAYS
        #ids_goodmuons = [ ]
        #for imuon in range(event.nMuon):
        #  if event.Muon_pt[imuon] < 20: continue
        #  if abs(event.Muon_eta[imuon]) > 2.4: continue
        #  if abs(event.Muon_dz[imuon]) > 0.2: continue
        #  if abs(event.Muon_dxy[imuon]) > 0.045: continue
        #  if not event.Muon_mediumId[imuon]: continue
        #  #if event.Muon_pfRelIso04_all[imuon]>0.50: continue
        #  ids_goodmuons.append(imuon)
        #if len(ids_goodmuons)<1: return False
        #idmax = max(ids_goodmuons,key=lambda i: event.Muon_pt[i])
        #self.out.fillBranch('pt_1',  event.Muon_pt[imuon])
        #self.out.fillBranch('eta_1', event.Muon_eta[imuon])
        #self.out.fillBranch('iso_1', event.Muon_pfRelIso04_all[imuon])
        
        # WITH OBJECT COLLECTION
        muons = [ ]
        for muon in Collection(event,'Muon'):
          if muon.pt < 20: continue
          if abs(muon.eta) > 2.4: continue
          if abs(muon.dz) > 0.2: continue
          if abs(muon.dxy) > 0.045: continue
          if not muon.mediumId: continue
          #if muon.pfRelIso04_all>0.50: continue
          muons.append(muon)
        if len(muons)<1: return False
        muon = max(muons,key=lambda p: p.pt)
        self.out.fillBranch('pt_1',  muon.pt)
        self.out.fillBranch('eta_1', muon.eta)
        self.out.fillBranch('iso_1', muon.pfRelIso04_all)
        
        return True
        

######################
#   POST-PROCESSOR   #
######################

# SETTING
outdir    = args.outdir
maxevts   = args.maxevts if args.maxevts>0 else None
nfiles    = -1
tag       = args.tag
tag       = ('' if not tag or tag.startswith('_') else '_') + tag
postfix   = "_test"+tag
url       = "root://cms-xrd-global.cern.ch/"
branchsel = None
infiles   = args.infiles or [
  #"data/DYJetsToLL_M-50_NanoAODv6.root",
  #"/afs/cern.ch/user/i/ineuteli/analysis/CMSSW_10_3_3/src/TauFW/PicoProducer/data/DYJetsToLL_M-50_NanoAODv6.root",
  url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/67/myNanoProdMc2017_NANO_66.root',
  url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/68/myNanoProdMc2017_NANO_67.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/69/myNanoProdMc2017_NANO_68.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/70/myNanoProdMc2017_NANO_69.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/71/myNanoProdMc2017_NANO_70.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/72/myNanoProdMc2017_NANO_71.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/73/myNanoProdMc2017_NANO_72.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/74/myNanoProdMc2017_NANO_73.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/75/myNanoProdMc2017_NANO_74.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/76/myNanoProdMc2017_NANO_75.root',
]
if nfiles>0: infiles = infiles[:nfiles]

# PRINT
print '-'*80
print ">>> %-10s = %s"%('maxevts',maxevts)
print ">>> %-10s = %r"%('outdir',outdir)
print ">>> %-10s = %r"%('postfix',postfix)
print ">>> %-10s = %s"%('infiles',infiles)
print ">>> %-10s = %r"%('branchsel',branchsel)
print '-'*80

# RUN
module = TestModule()
p = PostProcessor(outdir,infiles,cut=None,branchsel=branchsel,outputbranchsel=branchsel,noOut=False,
                  modules=[module],provenance=False,postfix=postfix,maxEntries=maxevts)
p.run()
print ">>> Done after %.1f seconds"%(time.time()-time0)
