# Author: Izaak Neutelings (January 2020)
# Sources:
#  https://twiki.cern.ch/twiki/bin/view/CMS/L1ECALPrefiringWeightRecipe
#  https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/modules/common/PrefireCorr.py
import os
from math import sqrt
from corrections import modulepath, extractTH1
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
path = os.path.join(os.getenv('CMSSW_BASE'),"src/PhysicsTools/NanoAODTools/data/prefire_maps/")


class PreFireTool():
    def __init__(self, year):
        
        dataset           = '2017BtoF' if year==2017 else '2016BtoH'
        jetfilename       = os.path.join(path,"L1prefiring_jetpt_%s.root"%dataset)
        photonfilename    = os.path.join(path,"L1prefiring_photonpt_%s.root"%dataset)
        jethistname       = "L1prefiring_jetpt_%s"%dataset
        photonhistname    = "L1prefiring_photonpt_%s"%dataset
        
        self.jetmap       = extractTH1(jetfilename,   jethistname)
        self.photonmap    = extractTH1(photonfilename,photonhistname)
        ###self.UseEMpT      = "jetempt" in jetroot
        self.JetMinPt     = 20 # Min/Max Values may need to be fixed for new maps
        self.JetMaxPt     = 500
        self.JetMinEta    = 2.0
        self.JetMaxEta    = 3.0
        self.PhotonMinPt  = 20
        self.PhotonMaxPt  = 500
        self.PhotonMinEta = 2.0
        self.PhotonMaxEta = 3.0
        
    
    def getWeight(self, event):
        """Get pre-fire weight"""
        
        # WEIGHTS
        weightDown = 1.
        weightNom  = 1.
        weightUp   = 1.
        
        # LOOP over JETS
        jets = Collection(event,'Jet')
        for jid, jet in enumerate(jets): # First loop over all jets
          jetpt = jet.pt
          ###if self.UseEMpT:
          ###  jetpt *= (jet.chEmEF + jet.neEmEF)
          
          if jetpt>=self.JetMinPt and self.JetMinEta<=abs(jet.eta)<=self.JetMaxEta:
            pfProbDown, pfProbNom, pfProbUp = self.getPrefireProbability(self.jetmap,jet.eta,jetpt,self.JetMaxPt)
            jetWeightDown = 1.-pfProbDown
            jetWeightNom  = 1.-pfProbNom
            jetWeightUp   = 1.-pfProbUp
          else:
            jetWeightDown = 1.0
            jetWeightNom  = 1.0
            jetWeightUp   = 1.0
          
          # The higher prefire-probablity between the jet and the lower-pt photon(s)/elecron(s) from the jet is chosen
          egWeightDown, egWeightNom, egWeightUp = self.getEGPrefireWeight(event,jid)
          weightDown *= min(jetWeightDown,egWeightDown)
          weightNom  *= min(jetWeightNom, egWeightNom)
          weightUp   *= min(jetWeightUp,  egWeightUp)
        
        # Then loop over all photons/electrons not associated to jets
        egWeightDown, egWeightNom, egWeightUp = self.getEGPrefireWeight(event,-1)
        weightDown *= egWeightDown
        weightNom  *= egWeightNom
        weightUp   *= egWeightUp
        
        return weightDown, weightNom, weightUp
        
    
    def getEGPrefireWeight(self, event, jid):
        egWeightDown = 1.0
        egWeightNom  = 1.0
        egWeightUp   = 1.0
        photonInJet  = [ ]
        
        # LOOP over PHOTONS
        for pid, pho in enumerate(Collection(event,'Photon')):
          if pho.jetIdx==jid and pho.pt>=self.PhotonMinPt and self.PhotonMinEta<=abs(pho.eta)<=self.PhotonMaxEta:
            phoProbDown, phoProbNom, phoProbUp = self.getPrefireProbability(self.photonmap,pho.eta,pho.pt,self.PhotonMaxPt)
            eleProbDown, eleProbNom, eleProbUp = 1., 1., 1.
            if pho.electronIdx>-1: # What if the electron corresponding to the photon would return a different value?
              if event.Electron_pt[pho.electronIdx]>=self.PhotonMinPt and self.PhotonMinEta<=abs(event.Electron_eta[pho.electronIdx])<=self.PhotonMaxEta:
                eleProbDown, eleProbNom, eleProbUp = self.getPrefireProbability(self.photonmap,event.Electron_eta[pho.electronIdx],event.Electron_pt[pho.electronIdx],self.PhotonMaxPt)
            
            # Choose higher prefire-probablity between the photon and corresponding electron
            egWeightDown *= 1.-max(phoProbDown,eleProbDown)
            egWeightNom  *= 1.-max(phoProbNom, eleProbNom)
            egWeightUp   *= 1.-max(phoProbUp,  eleProbUp)
            photonInJet.append(pid)
        
        # LOOP over ELECTRONS
        for ele in Collection(event,'Electron'):
          if ele.jetIdx == jid and ele.photonIdx not in photonInJet and ele.pt>=self.PhotonMinPt and self.PhotonMinEta<=abs(ele.eta)<=self.PhotonMaxEta:
            pfProbDown, pfProbNom, pfProbUp = self.getPrefireProbability(self.photonmap,ele.eta,ele.pt,self.PhotonMaxPt)
            egWeightDown *= 1.-pfProbDown
            egWeightNom  *= 1.-pfProbNom
            egWeightUp   *= 1.-pfProbUp
        
        return egWeightDown, egWeightNom, egWeightUp
        
    
    def getPrefireProbability(self, map, eta, pt, maxpt):
      bin      = map.FindBin(eta,min(pt,maxpt-0.01))
      prob     = map.GetBinContent(bin)
      stat     = map.GetBinError(bin) # bin statistical uncertainty
      syst     = 0.2*prob # 20% of prefire rate
      probDown = max(prob-sqrt(stat*stat+syst*syst),0.0)
      probUp   = min(prob+sqrt(stat*stat+syst*syst),1.0)
      return probDown, prob, probUp
      
