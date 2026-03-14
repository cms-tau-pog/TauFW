# Skimmer for CMSDAS2025, Author: Andrea Cardini (Sept 2025)
# Core idea: dump into a TauTuple the tau collection and the gen properties of corresponding GenVisTau objects

from ROOT import TFile, TTree
import sys, re
from math import sqrt, exp, cos
from ROOT import TLorentzVector, TVector3
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.common.tools.log import header
from TauFW.PicoProducer.analysis.utils import ensurebranches, redirectbranch, matchgenvistau, deltaR
from TauFW.PicoProducer.analysis.TauTreeProducer import *


class TauVarDumper(Module):

    def __init__(self, fname, **kwargs):
        print(header(self.__class__.__name__))
        
        # SETTINGS
        self.filename   = fname # output file name
        self.dtype      = kwargs.get('dtype',    'mc')
        self.ismc       = self.dtype=='mc'
        self.channel    = kwargs.get('channel',  'tau'         ) # channel name
        self.year       = kwargs.get('year',     2024           ) # integer, e.g. 2017, 2018
        self.era        = kwargs.get('era',      '2024'   ) # string, e.g. '2017', 'UL2017'
        self.verbosity  = kwargs.get('verb',     0              ) # verbosity
        self.out = TauTree(fname,self)

        assert self.dtype in ['mc'], "Did not recognize data type '%s'! Please choose from 'mc', 'data' and 'embed'."%self.dtype
    

    def beginJob(self):
        """Before processing any events or files."""
        print('-'*80)
        print(">>> %-12s = %r"%('filename',  self.filename))
        print(">>> %-12s = %s"%('year',      self.year))
        print(">>> %-12s = %r"%('dtype',     self.dtype))
        print(">>> %-12s = %r"%('channel',   self.channel))

    def endJob(self):
        self.out.endJob()

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        """Before processing a new file."""
        sys.stdout.flush()
        
    def analyze(self, event):
        sys.stdout.flush()
        taus   = Collection(event, 'Tau')

        for tau in taus:

            self.out.run[0]             = event.run
            self.out.evt[0]           = event.event

            self.out.tau_eta[0]  = tau.eta
            self.out.tau_phi[0]  = tau.phi
            self.out.tau_mass[0] = tau.mass
            self.out.tau_dm[0]   = tau.decayMode
            self.out.tau_pt[0]   = tau.pt
            self.out.tau_ptCorrPNet[0]   = tau.ptCorrPNet
            self.out.tau_ptCorrUParT[0]   = tau.ptCorrUParT
            self.out.tau_puCorr[0]   = tau.puCorr

            gentau_pt, gentau_eta, gentau_phi, gentau_dm = matchgenvistau(event,tau)
            self.out.tau_genpt[0]   = gentau_pt
            self.out.tau_geneta[0]  = gentau_eta
            self.out.tau_genphi[0]  = gentau_phi
            self.out.tau_gendm[0]   = gentau_dm

            
            self.out.tau_charge[0] = tau.charge
            self.out.tau_qConfPNet[0] = tau.qConfPNet
            self.out.tau_qConfUParT[0] = tau.qConfUParT

            
            self.out.tau_nSVs[0] = tau.nSVs
            self.out.tau_ipLengthSig[0] = tau.ipLengthSig
            self.out.tau_IPx[0] = tau.IPx
            self.out.tau_IPy[0] = tau.IPy
            self.out.tau_IPz[0] = tau.IPz
            self.out.tau_dxy[0] = tau.dxy
            self.out.tau_dz[0]  = tau.dz
            
            self.out.tau_decayModePNet[0] = tau.decayModePNet
            self.out.tau_decayModeUParT[0] = tau.decayModeUParT
            self.out.tau_idDecayModeNewDMs[0] = tau.idDecayModeNewDMs
            self.out.tau_idDecayModeOldDMs[0] = tau.idDecayModeOldDMs
            self.out.tau_idAntiMu[0] = tau.idAntiMu
            
            self.out.tau_leadTkDeltaEta[0] = tau.leadTkDeltaEta
            self.out.tau_leadTkDeltaPhi[0] = tau.leadTkDeltaPhi
            self.out.tau_leadTkPtOverTauPt[0] = tau.leadTkPtOverTauPt
            
            self.out.tau_rawDeepTau2018v2p5VSe[0]    = tau.rawDeepTau2018v2p5VSe
            self.out.tau_rawDeepTau2018v2p5VSmu[0]   = tau.rawDeepTau2018v2p5VSmu
            self.out.tau_rawDeepTau2018v2p5VSjet[0]  = tau.rawDeepTau2018v2p5VSjet
            self.out.tau_rawIso[0] = tau.rawIso
            self.out.tau_rawIsodR03[0] = tau.rawIsodR03
            self.out.tau_rawPNetVSe[0] = tau.rawPNetVSe
            self.out.tau_rawPNetVSjet[0] = tau.rawPNetVSjet
            self.out.tau_rawPNetVSmu[0] = tau.rawPNetVSmu
            self.out.tau_rawUParTVSe[0] = tau.rawUParTVSe
            self.out.tau_rawUParTVSjet[0] = tau.rawUParTVSjet
            self.out.tau_rawUParTVSmu[0] = tau.rawUParTVSmu
            
            self.out.tau_refitSVchi2[0] = tau.refitSVchi2
            self.out.tau_refitSVcov00[0] = tau.refitSVcov00
            self.out.tau_refitSVcov10[0] = tau.refitSVcov10
            self.out.tau_refitSVcov11[0] = tau.refitSVcov11
            self.out.tau_refitSVcov20[0] = tau.refitSVcov20
            self.out.tau_refitSVcov21[0] = tau.refitSVcov21
            self.out.tau_refitSVcov22[0] = tau.refitSVcov22
            
            self.out.tau_refitSVx[0] = tau.refitSVx
            self.out.tau_refitSVy[0] = tau.refitSVy
            self.out.tau_refitSVz[0] = tau.refitSVz
            self.out.tau_photonsOutsideSignalCone[0] = tau.photonsOutsideSignalCone
            
            self.out.fill()

        return True
