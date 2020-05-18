#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Simple module to nanoAOD post-processing
import time; time0 = time.time()
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

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
