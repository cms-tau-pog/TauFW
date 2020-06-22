# Author: Izaak Neutelings (June 2020)
# Description: Quick generator-level checks of LQ samples
from ROOT import TFile, TTree, TH1D
import numpy as np
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from TauFW.PicoProducer.analysis.TreeProducerBase import TreeProducerBase
from TauFW.PicoProducer.analysis.utils import dumpgenpart


class ModuleGenLQ(Module):
  
  def __init__(self,fname):
    self.out      = TreeProducerBase(fname,self)
    self.out.addBranch('genweight',    'f')
    self.out.addBranch('nlqs',         'i')
    self.out.addBranch('nvistaus',     'i')
    self.out.addBranch('ntaus',        'i')
    self.out.addBranch('ntnus',        'i')
    self.out.addBranch('ntops',        'i')
    self.out.addBranch('pt_lq1',       'f')
    self.out.addBranch('pt_lq2',       'f')
    self.out.addBranch('dau1_lq1',     'f')
    self.out.addBranch('dau1_lq2',     'f')
    self.out.addBranch('dau2_lq1',     'f')
    self.out.addBranch('dau2_lq2',     'f')
    self.out.addBranch('pt_vistau1',   'f')
    self.out.addBranch('pt_vistau2',   'f')
    self.out.addBranch('moth_vistau1', 'f')
    self.out.addBranch('moth_vistau2', 'f')
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.Fill(0)
    
    # LQs
    lqs      = [ ]
    lqids    = [46,9000002,9000006]
    genparts = Collection(event,'GenPart')
    taus     = [ ]
    tnus     = [ ]
    tops     = [ ]
    #print '-'*80
    for part in genparts:
      pid = abs(part.pdgId)
      #dumpgenpart(part,genparts=genparts)
      if pid in lqids:
        if part.status<60: continue
        for i, lq in enumerate(lqs):
          if lq._index==part.genPartIdxMother and lq.pdgId==part.pdgId:
            lqs[i] = part
            break
        else:
          part.decays = [ ]
          lqs.append(part)
      else:
        for lq in lqs:
          if lq._index==part.genPartIdxMother:
            lq.decays.append(pid)
        if pid==6:
          for i, top in enumerate(tops):
            if top._index==part.genPartIdxMother and top.pdgId==part.pdgId:
              tops[i] = part
              break
          else:
            tops.append(part)
        elif pid==15:
          for i, tau in enumerate(taus):
            if tau._index==part.genPartIdxMother and tau.pdgId==part.pdgId:
              taus[i] = part
              break
          else:
            taus.append(part)
        elif pid==16:
          tnus.append(part)
    
    # TAUS
    vistaus = [ ]
    for vistau in Collection(event,'GenVisTau'):
      vistau.mother = -1
      for tau in taus:
        if tau.DeltaR(vistau)>0.3: continue
        moth = tau
        while moth.genPartIdxMother>=0:
          moth = genparts[moth.genPartIdxMother]
          if abs(moth.pdgId)!=15:
            vistau.mother = moth.pdgId
            break
        break
      #moth = vistau
      #while moth.genPartIdxMother>=0:
      #  moth = genparts[moth.genPartIdxMother]
      #  if abs(moth.pdgId)!=15:
      #    vistau.mother = moth.pdgId
      #    break
      vistaus.append(vistau)
    
    # SAVE VARIABLES
    self.out.genweight[0]  = event.genWeight
    self.out.nlqs[0]       = len(lqs)
    self.out.ntaus[0]      = len(taus)
    self.out.ntnus[0]      = len(tnus)
    self.out.nvistaus[0]   = len(vistaus)
    self.out.ntops[0]      = len(tops)
    if len(lqs)>=2:
      lqs[0].decays.sort()
      lqs[1].decays.sort()
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = lqs[1].pt
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = lqs[1].decays[0] if len(lqs[1].decays)>=1 else -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = lqs[1].decays[1] if len(lqs[1].decays)>=2 else -1
    elif len(lqs)>=1:
      lqs[0].decays.sort()
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = -1
    else:
      self.out.pt_lq1[0]   = -1
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = -1
      self.out.dau2_lq2[0] = -1
    if len(vistaus)>=2:
      self.out.pt_vistau1[0]   = vistaus[0].pt
      self.out.pt_vistau2[0]   = vistaus[1].pt
      self.out.moth_vistau1[0] = vistaus[0].mother
      self.out.moth_vistau2[0] = vistaus[1].mother
    elif len(vistaus)>=1:
      self.out.pt_vistau1[0]   = vistaus[0].pt
      self.out.pt_vistau2[0]   = -1
      self.out.moth_vistau1[0] = vistaus[0].mother
      self.out.moth_vistau2[0] = -1
    else:
      self.out.pt_vistau1[0]   = -1
      self.out.pt_vistau2[0]   = -1
      self.out.moth_vistau1[0] = -1
      self.out.moth_vistau2[0] = -1
    self.out.Fill()
    
    return True
