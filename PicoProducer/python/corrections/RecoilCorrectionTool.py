#! /bin/usr/env python
# Author: Izaak Neutelings (November 2018)
# https://github.com/CMS-HTT/RecoilCorrections
# https://twiki.cern.ch/twiki/bin/view/CMS/MSSMAHTauTauEarlyRun2#Top_quark_pT_reweighting
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/TopPtReweighting#MC_SFs_Reweighting
# https://twiki.cern.ch/twiki/bin/view/CMS/TopPtReweighting
import os
from math import sqrt, exp
from ctypes import c_float
from TauFW.PicoProducer import datadir
from TauFW.common.tools.file import ensureTFile
from TauFW.PicoProducer.analysis.utils import hasbit
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
import ROOT
from ROOT import TLorentzVector, gROOT, gSystem, gInterpreter, Double
rcpath  = "HTT-utilities/RecoilCorrections/data/"
zptpath = os.path.join(datadir,"zpt/")



class ZptCorrectionTool:
  
  def __init__(self, era):
    """Load Z pT weights."""
    #assert year in [2016,2017,2018], "ZptCorrectionTool: You must choose a year from: 2016, 2017, or 2018."
    filename = None
    if 'UL' in era and False:
      if '2016' in era and 'preVFP' in era:
        filename = zptpath+"Zpt_weights_UL2016_preVFP.root"
      elif '2016' in era:
        filename = zptpath+"Zpt_weights_UL2016_postVFP.root"
      elif '2017' in era:
        filename = zptpath+"Zpt_weights_UL2017.root"
      elif '2018' in era:
        filename = zptpath+"Zpt_weights_UL2018.root"
    else:
      if '2016' in era:
        filename = zptpath+"Zpt_weights_2016.root"
      elif '2017' in era:
        filename = zptpath+"Zpt_weights_2017.root"
      elif '2018' in era:
        filename = zptpath+"Zpt_weights_2018.root"
    assert filename!=None, "ZptCorrectionTool.__init__: Did not find filename for %r"%(era)
    file    = ensureTFile(filename,'READ')
    hist = file.Get('zptmass_weights')
    hist.SetDirectory(0)
    file.Close()
    self.hist     = hist
    self.filename = filename
  
  def getZptWeight(self,Zpt,Zmass):
    """Get Z pT weight for a given Z boson pT and mass."""
    xbin = self.hist.GetXaxis().FindBin(Zmass)
    ybin = self.hist.GetYaxis().FindBin(Zpt)
    if xbin==0: xbin = 1 # underflow: use first bin
    elif xbin>self.hist.GetXaxis().GetNbins(): xbin -= 1 # overflow: use last bin
    if ybin==0: ybin = 1 # underflow: use first bin
    elif ybin>self.hist.GetYaxis().GetNbins(): ybin -= 1 # overflow: use last bin
    weight = self.hist.GetBinContent(xbin,ybin)
    return weight
  


class RecoilCorrectionTool:
  
  def __init__(self, year=2017, dozpt=True):
    """Load correction tool."""
    assert year in [2016,2017,2018], "RecoilCorrectionTool: You must choose a year from: 2016, 2017, or 2018."        
    if year==2016:
      filename = rcpath+"TypeI-PFMet_Run2016BtoH.root" #"TypeI-PFMet_Run2016_legacy.root"
    elif year==2017:
      filename = rcpath+"Type1_PFMET_2017.root"
    else:
      filename = rcpath+"TypeI-PFMet_Run2018.root"
    print "Loading RecoilCorrectionTool(%s)..."%filename
    CMSSW_BASE = os.environ.get("CMSSW_BASE",None)
    recoil_h   = "%s/src/HTT-utilities/RecoilCorrections/interface/RecoilCorrector.h"%(CMSSW_BASE)
    assert CMSSW_BASE, "RecoilCorrectionTool: Did not find $CMSSW_BASE"
    assert os.path.isfile(recoil_h), "RecoilCorrectionTool: Did not find RecoilCorrection header: %s"%recoil_h
    gROOT.ProcessLine('#include "%s"'%recoil_h)
    gSystem.Load("libHTT-utilitiesRecoilCorrections.so")
    corrector  = ROOT.RecoilCorrector(filename)
    self.corrector = corrector
    self.filename  = filename
    
  def CorrectPFMETByMeanResolution(self, met, boson, boson_vis, njets):
    """Correct PF MET using the full and visibile boson Lorentz vector."""
    metpx_corr, metpy_corr = c_float(), c_float()
    #print "before: met pt = %4.1f, phi = %4.1f, px = %4.1f, py = %4.1f; boson px = %4.1f, py = %4.1f; vis. boson px = %4.1f, py = %4.1f; njets = %d"%(met.Pt(),met.Phi(),met.Px(),met.Py(),boson.Px(),boson.Py(),boson_vis.Px(),boson_vis.Py(),njets)
    self.corrector.CorrectByMeanResolution(met.Px(),met.Py(),boson.Px(),boson.Py(),boson_vis.Px(),boson_vis.Py(),njets,metpx_corr,metpy_corr)
    met.SetPxPyPzE(metpx_corr.value,metpy_corr.value,0.,sqrt(metpx_corr.value**2+metpy_corr.value**2))
    #print "after:  met pt = %4.1f, phi = %4.1f, px = %4.1f, py = %4.1f, metpx_corr.value = %.1f, metpy_corr.value = %.1f"%(met.Pt(),met.Phi(),met.Px(),met.Py(),metpx_corr.value,metpy_corr.value)
    return met
  

def getTopPtWeight(toppt1,toppt2):
  """Get top pT weight."""
  #sqrt(exp(0.156-0.00137*min(toppt1,400.0))*exp(0.156-0.00137*min(toppt2,400.0)))
  return sqrt(exp(0.0615-0.0005*min(toppt1,800.0))*exp(0.0615-0.0005*min(toppt2,800.0)))
  

def getzboson(event):
  """Calculate Z boson pT and mass."""
  #print '-'*80
  particles  = Collection(event,'GenPart')
  zboson     = TLorentzVector()
  for id in range(event.nGenPart):
    particle = particles[id]
    PID      = abs(particle.pdgId)
    if ((PID==11 or PID==13) and particle.status==1 and hasbit(particle.statusFlags,8)) or\
                   (PID==15  and particle.status==2 and hasbit(particle.statusFlags,8)):
      zboson += particle.p4()
      #print "%3d: PID=%3d, mass=%3.1f, pt=%4.1f, status=%2d, statusFlags=%5d (%16s), fromHardProcess=%1d, isHardProcessTauDecayProduct=%1d, isDirectHardProcessTauDecayProduct=%1d"%\
      #(id,particle.pdgId,particle.mass,particle.pt,particle.status,particle.statusFlags,bin(particle.statusFlags),hasbit(particle.statusFlags,8),hasbit(particle.statusFlags,9),hasbit(particle.statusFlags,10))
  #print "tlv: mass=%3.1f, pt=%3.1f"%(zboson.M(),zboson.Pt())
  return zboson
  

def getboson(event):
  """Calculate Z/W/H boson full and visible pT and mass, for recoil corrections."""
  #print '-'*80
  particles  = Collection(event,'GenPart')
  #boson_real = TLorentzVector()
  boson_full = TLorentzVector()
  boson_vis  = TLorentzVector()
  for id in range(event.nGenPart):
    particle = particles[id]
    PID      = abs(particle.pdgId)
    neutrino = PID in [12,14,16]
    #if PID in [23,24,25] and particle.status==62:
    #  boson_real = particle.p4()
    #  print "%3d: PID=%3d, mass=%3.1f, pt=%3.1f, status=%2d"%(id,particle.pdgId,particle.mass,particle.pt,particle.status)
    if ((PID==11 or PID==13 or neutrino) and particle.status==1 and hasbit(particle.statusFlags,8)) or hasbit(particle.statusFlags,10):
      boson_full += particle.p4()
      if not neutrino:
        boson_vis += particle.p4()
      #print "%3d: PID=%3d, mass=%3.1f, pt=%4.1f, status=%2d, statusFlags=%5d (%16s), fromHardProcess=%1d, isHardProcessTauDecayProduct=%1d, isDirectHardProcessTauDecayProduct=%1d"%\
      #(id,particle.pdgId,particle.mass,particle.pt,particle.status,particle.statusFlags,bin(particle.statusFlags),hasbit(particle.statusFlags,8),hasbit(particle.statusFlags,9),hasbit(particle.statusFlags,10))
  #print "real: mass=%3.1f, pt=%3.1f"%(boson_real.M(),boson_real.Pt())
  #print "full: mass=%3.1f, pt=%3.1f"%(boson_full.M(),boson_full.Pt())
  #print "vis:  mass=%3.1f, pt=%3.1f"%(boson_vis.M(),boson_vis.Pt())
  return boson_full, boson_vis
  

def gettoppt(event):
  """Calculate top pT."""
  #print '-'*80
  particles = Collection(event,'GenPart')
  toppt1    = -1
  toppt2    = -1
  for id in range(event.nGenPart):
    particle = particles[id]
    PID      = abs(particle.pdgId)
    if PID==6 and particle.status==62:
      #print "%3d: PID=%3d, mass=%3.1f, pt=%3.1f, status=%2d"%(id,particle.pdgId,particle.mass,particle.pt,particle.status)
      if particle.pt>toppt1:
        if toppt1==-1:
          toppt1 = particle.pt
        else:
          toppt2 = toppt1
          toppt1 = particle.pt
      else:
        toppt2 = particle.pt
  return toppt1, toppt2
  
