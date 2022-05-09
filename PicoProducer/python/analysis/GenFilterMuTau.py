#! /usr/bin/env python
# Author: Izaak Neutelings (May 2022)
# Description: Study gen filter of mutau events for stitching of DYJetsToLL_M-50
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/MCStitching
# Instructions:
#   pico.py channel genmutau GenFilterMuTau
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import re
from ROOT import TH1D, TH2D, gStyle, kRed
from TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.PicoProducer.analysis.utils import hasbit


class GenFilterMuTau(Module):
  """Simple module to study decays and gen filters in DY samples."""
  
  def __init__(self,fname,**kwargs):
    self.out = TreeProducerGenFilterMuTau(fname,self)
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('none')
    self.out.h_nup.Fill(event.LHE_Njets)
    #self.out.h_weight.Fill(event.LHE_Njets)
    
    # SELECT PROMPT CANDIDATES
    #elecs        = [ ] # prompt elecs
    muons        = [ ] # prompt muons
    elecs_hard   = [ ] # prompt electrons from hard process
    muons_hard   = [ ] # prompt muons from hard process
    taus_hard    = [ ] # prompt taus from hard process
    elecs_tau    = [ ] # electrons from decay of prompt tau
    muons_tau    = [ ] # muons from decay of prompt tau
    particles = Collection(event,'GenPart')
    for particle in particles:
      pid = abs(particle.pdgId)
      ###dumpgenpart(particle,genparts=particles,flags=[3,4,5,6,8,9,10])
      if pid==11:
        # 9: isHardProcessTauDecayProduct, 10: isDirectHardProcessTauDecayProduct
        if (hasbit(particle.statusFlags,9) or hasbit(particle.statusFlags,10)):
          elecs_tau.append(particle)
        elif hasbit(particle.statusFlags,8): # fromHardProcess
          elecs_hard.append(particle)
      elif pid==13:
        muons.append(particle)
        # 9: isHardProcessTauDecayProduct, 10: isDirectHardProcessTauDecayProduct
        if (hasbit(particle.statusFlags,9) or hasbit(particle.statusFlags,10)):
          muons_tau.append(particle)
        elif hasbit(particle.statusFlags,8): # fromHardProcess
          muons_hard.append(particle)
      elif pid==15:
        if particle.status==2 and hasbit(particle.statusFlags,8): # fromHardProcess
          taus_hard.append(particle)
        #else:
        #  taus_hard.append(particle)
    
    # HADRONIC TAUS
    tauhs_hard = [ ] # hadronic tau from prompt tau
    genvistaus = Collection(event,'GenVisTau')
    if len(taus_hard)>=2:
      #print '-'*20+" 2 taus "
      for tau in taus_hard:
        dRmin = 1.0
        match = None
        for genvistau in genvistaus:
          dR = tau.DeltaR(genvistau)
          if dR<dRmin:
            dRmin = dR
            match = genvistau
        if match:
          self.out.h_dR_tauh.Fill(dRmin)
          if dRmin<0.5: # and genvistau in tauhs_hard
            tauhs_hard.append(match)
    
    # FILL HISTOGRAMS
    self.out.h_nelec_vs_ntau.Fill(len(elecs_hard),len(taus_hard))
    self.out.h_nmuon_vs_ntau.Fill(len(muons_hard),len(taus_hard))
    self.out.h_nmuon_vs_ntauh.Fill(len(muons_hard),len(tauhs_hard))
    if len(elecs_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('ee')
    if len(muons_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('mumu')
    if len(taus_hard)>=2:
      self.out.cutflow.fill('ll')
      self.out.cutflow.fill('tautau')
    elif len(elecs_hard)<2 and len(muons_hard)<2:
      self.out.cutflow.fill('unknown')
    
    # TAU DECAYS
    if len(elecs_tau)==1 and len(tauhs_hard)==1:
      self.out.cutflow.fill('etauh')
    if len(muons_tau)==1 and len(tauhs_hard)==1:
      self.out.cutflow.fill('mutauh')
    if len(tauhs_hard)==2:
      self.out.cutflow.fill('tauhtauh')
    if len(elecs_tau)+len(muons_tau)==2:
      self.out.cutflow.fill('taultaul')
    
    if len(muons)==0 and len(genvistaus)==0:
      return False
    
    ## FILL TREE BRANCHES
    #self.out.pt[0]                     = tau.pt
    self.out.nelecs[0]                  = len(elecs_hard)
    self.out.nmuons[0]                  = len(muons_hard)
    self.out.ntaus[0]                   = len(taus_hard)
    self.out.fill()
    
    return True
    

class TreeProducerGenFilterMuTau(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerGenFilterMuTau,self).__init__(filename,module,**kwargs)
    
    # CUTFLOW
    self.cutflow.addcut('none',    "no cut"   )
    self.cutflow.addcut('ll',      "ll"       )
    self.cutflow.addcut('ee',      "ee"       )
    self.cutflow.addcut('mumu',    "mumu"     )
    self.cutflow.addcut('tautau',  "tautau"   )
    self.cutflow.addcut('unknown', "unknown"  )
    self.cutflow.addcut('etauh',   "etauh"    )
    self.cutflow.addcut('mutauh',  "mutauh"   )
    self.cutflow.addcut('tauhtauh',"tauhtauh" )
    self.cutflow.addcut('taultaul',"taultaul" )
    
    # HISTOGRAMS
    self.h_nup     = TH1D('h_nup',";Number of partons at LHE level;MC events",9,0,9)
    self.h_dR_tauh = TH1D('h_dR_tauh',";#DeltaR(#tau,#tau);Tau leptons",5,0,5)
    self.h_nelec_vs_ntau  = TH2D('h_nelec_vs_ntau', ";Number of electrons from hard process;Number of taus from hard process",8,0,8,8,0,8)
    self.h_nmuon_vs_ntau  = TH2D('h_nmuon_vs_ntau', ";Number of muons from hard process;Number of #tau leptons from hard process",8,0,8,8,0,8)
    self.h_nmuon_vs_ntauh = TH2D('h_nmuon_vs_ntauh',";Number of muons from hard process;Number of #tau_{#lower[-0.2]{h}} from hard process",8,0,8,8,0,8)
    
    # TREE BRANCHES
    #self.addBranch('pt',           'f')
    self.addBranch('nelecs',        'i', title="number of prompt gen electrons")
    self.addBranch('nmuons',        'i', title="number of prompt gen muons")
    self.addBranch('ntaus',         'i', title="number of prompt gen taus")
    
  def endJob(self):
    """Write and close files after the job ends."""
    ntau  = self.cutflow.getbincontent('tautau')
    ntau_ = 0
    if ntau>0:
      print ">>> Ditau decays:"
      for bin, exp in [('etauh',23),('mutauh',23),('tauhtauh',42),('taultaul',12)]:
        nbin = self.cutflow.getbincontent(bin)
        ntau_ += nbin
        print ">>> %14.1f / %.1f = %5.2f%%   %s, expect %s%%"%(nbin,ntau,100.0*nbin/ntau,bin,exp)
      print ">>> %14.1f / %.1f = %5.2f%%"%(ntau_,ntau,100.0*ntau_/ntau)
    else:
      print ">>> No ditau..."
    super(TreeProducerGenFilterMuTau,self).endJob()
  
