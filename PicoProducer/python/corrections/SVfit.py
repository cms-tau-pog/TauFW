# Author: Izaak Neutelings (June 2024)
# Instructions:
#   cd $CMSSW_BASE/src/
#   cmsenv
#   git clone https://github.com/SVfit/ClassicSVfit TauAnalysis/ClassicSVfit -b fastMTT_19_02_2019
#   git clone https://github.com/SVfit/SVfitTF TauAnalysis/SVfitTF
#   cd $CMSSW_BASE/src
#   scram b -j8
# Sources:
#   https://arxiv.org/abs/1603.05910
#   https://indico.cern.ch/event/684622/#12-svfit
#   https://github.com/SVfit/ClassicSVfit (recommended version)
#   https://github.com/SVfit/SVfitTF (dependency in ClassicSVfit)
#   https://github.com/adewit/NanoToolsInterface (nanoAOD-tools/python interface)
from TauFW.common.tools.log import Logger
from math import cos, sin
LOG = Logger('SVfit',showname=True)
from ROOT import gSystem, gROOT, TMatrixD, vector


# LOAD LIBRARY
try:
  # https://github.com/SVfit/ClassicSVfit/blob/fastMTT_19_02_2019/interface/FastMTT.h
  # https://github.com/SVfit/ClassicSVfit/blob/master/interface/MeasuredTauLepton.h
  print("Loading SVfit libraries...")
  gROOT.ProcessLine('#include "TauAnalysis/ClassicSVfit/interface/FastMTT.h"')
  gROOT.ProcessLine('#include "TauAnalysis/ClassicSVfit/interface/MeasuredTauLepton.h"')
  gSystem.Load('$CMSSW_BASE/lib/$SCRAM_ARCH/libTauAnalysisNanoToolsInterface.so')
  #gROOT.ProcessLine('#include "TauAnalysis/NanoToolsInterface/interface/InterfaceFastMTT.h"')
  from ROOT import FastMTT
  from ROOT.classic_svFit import MeasuredTauLepton # kTauToElecDecay, kTauToMuDecay, kTauToHadDecay
  print("Loaded SVfit libraries!")
except Exception as error:
  LOG.throw(error,"Failed to load SVfit libraries...")


class SVfit:
  
  def __init__(self,channel,verb=0):
    """Prepare fast SVfit tool."""
    
    # CHANNELS
    #assert(channel in ['mutau','eletau','tautau','mumu']), "SVfit: You must choose a channel from: mutau, eletau, tautau, mumu!"
    self.channel = channel
    if 'tautau' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToHadDecay
      self.decaytype2 = MeasuredTauLepton.kTauToHadDecay
    elif 'etau' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToElecDecay
      self.decaytype2 = MeasuredTauLepton.kTauToHadDecay
    elif 'mutau' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToMuDecay
      self.decaytype2 = MeasuredTauLepton.kTauToHadDecay
    elif 'emu' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToElecDecay
      self.decaytype2 = MeasuredTauLepton.kTauToMuDecay
    elif 'mumu' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToMuDecay
      self.decaytype2 = MeasuredTauLepton.kTauToMuDecay
    elif 'ee' in channel:
      self.decaytype1 = MeasuredTauLepton.kTauToElecDecay
      self.decaytype2 = MeasuredTauLepton.kTauToElecDecay
    else:
      LOG.throw(OSError,f"Did not recognize channel {channel!r}...")
    
    # PREPARE OBJECTS (C++)
    if verb+2>=1:
      print(f"Loading SVfit for channel {channel!r} with decay types=({self.decaytype1},{self.decaytype2})...")
    self.fastmtt = FastMTT()
    self.covMET  = TMatrixD(2,2) # 2x2 covariant MET matrix, allocate once !
    self.vec_tt  = vector('classic_svFit::MeasuredTauLepton')() # allocate once !
    
    # SET PARAMETERS
    #shapeparams = vector('double')([6,1.0/1.15]) # power of 1/mVis, and scaling factor of mTest
    #self.fastmtt.setLikelihoodParams(shapeparams)
    
  def run(self,tau1,tau2,metpt,metphi,covMETXX,covMETXY,covMETYY):
    """Set both tau candidate legs & MET, and return best ."""
    # https://github.com/adewit/NanoToolsInterface/blob/master/src/InterfaceFastMTT.cc
    # https://github.com/adewit/NanoToolsInterface/blob/master/interface/InterfaceFastMTT.h
    # https://cms-nanoaod-integration.web.cern.ch/integration/cms-swCMSSW_12_4_X/data124Xrun3_v10_doc.html#MET
    dm1  = tau1.decayMode if self.decaytype1==MeasuredTauLepton.kTauToHadDecay else -1
    dm2  = tau2.decayMode if self.decaytype2==MeasuredTauLepton.kTauToHadDecay else -1
    leg1 = MeasuredTauLepton(self.decaytype1,tau1.pt,tau1.eta,tau1.phi,tau1.mass,dm1)
    leg2 = MeasuredTauLepton(self.decaytype2,tau2.pt,tau2.eta,tau2.phi,tau2.mass,dm2)
    self.covMET[0][0] = covMETXX #met.covXX
    self.covMET[1][0] = covMETXY #met.covXY
    self.covMET[0][1] = covMETXY #met.covXY # = covYX
    self.covMET[1][1] = covMETYY #met.covYY
    metx = metpt*cos(metphi)
    mety = metpt*sin(metphi)
    self.vec_tt.clear() # empty vector
    self.vec_tt.push_back(leg1)
    self.vec_tt.push_back(leg2)
    self.fastmtt.run(self.vec_tt, metx, mety, self.covMET)
    tlv_tt = self.fastmtt.getBestP4()
    return tlv_tt
    

def testSVfit():
  # https://github.com/SVfit/ClassicSVfit/blob/fastMTT_19_02_2019/bin/testClassicSVfit.cc
  # Instructions:
  #   from TauFW.PicoProducer.corrections.SVfit import testSVfit
  #   from timeit import timeit
  #   timeit('testSVfit()', number=100, setup="from __main__ import testSVfit")
  #print(">>> testSVfit: Initializing SVfit...")
  sfvit  = SVfit('etau')
  #print(">>> testSVfit: Setting etau legs...")
  leg1   = MeasuredTauLepton(MeasuredTauLepton.kTauToElecDecay,33.7393,0.940900,-0.541458,0.51100e-3) # tau -> electron decay (Pt, eta, phi, mass)
  leg2   = MeasuredTauLepton(MeasuredTauLepton.kTauToHadDecay, 25.7322,0.618228, 2.793620,0.13957, 0) # tau -> 1prong0pi0 hadronic decay (Pt, eta, phi, mass)
  vec_tt = sfvit.vec_tt # 2x2 covariant MET matrix, allocate once !
  vec_tt.clear()
  vec_tt.push_back(leg1)
  vec_tt.push_back(leg2)
  #print(">>> testSVfit: Setting covMET...")
  covMET = sfvit.covMET # 2x2 covariant MET matrix, allocate once !
  covMET[0][0] =  787.352 # covXX
  covMET[1][0] = -178.630 # covXY
  covMET[0][1] = -178.630 # covYX
  covMET[1][1] =  179.545 # covYY
  metx =  11.7491
  mety = -51.9172
  #print(">>> testSVfit: run!")
  fastmtt = sfvit.fastmtt
  fastmtt.run(vec_tt,metx,mety,covMET)
  tlv_tt = fastmtt.getBestP4()
  print(tlv_tt,tlv_tt.M()) # expect m = 108.991
  return tlv_tt
  
