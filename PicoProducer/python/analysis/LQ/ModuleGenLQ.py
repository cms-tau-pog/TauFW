#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2020)
# Description:
#   Simple example of gen-level study of LQ samples.
#   This analysis module selects interesting particles for various LQ processes,
#   and creates an output file with a single flat tree for several kinematic variables.
# Instructions to run standalone:
#   python3 python/analysis/LQ/ModuleGenLQ.py --lq t -t _nonres -n 10000
# Instructions to run with pico.py:
#   pico.py channel lq python/analysis/LQ/ModuleGenLQ.py
#   pico.py run -c lq -y UL2018 -s LQ -n 10000
# Sources:
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc106Xul18_doc.html#GenPart
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/genparticles_cff.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/LHETablesProducer.cc
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/examples/exampleGenDump.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/GenDumper.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/LQ/ModuleGenLQ.py
#   https://pdg.lbl.gov/2023/reviews/rpp2022-rev-monte-carlo-numbering.pdf (PDG ID)
#   https://pythia.org/latest-manual/ParticleProperties.html (Pythia particle status)
from __future__ import print_function # for python3 compatibility
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.analysis.utils import dumpgenpart, getmother
#import PhysicsTools.NanoAODTools.postprocessing.framework.datamodel as datamodel
#from TauFW.PicoProducer.analysis.utils import dumpgenpart
#datamodel.statusflags['isHardPrompt'] = datamodel.statusflags['isPrompt'] + datamodel.statusflags['fromHardProcess'] 


def getdRmin(part,oparts):
  """Find DeltaR with closest particle."""
  dRmin = 10 if oparts else -1
  for opart in oparts:
    dR = part.DeltaR(opart)
    if dR<dRmin:
      dRmin = dR
  return dRmin
  

# DUMPER MODULE
class ModuleGenLQ(Module):
  
  def __init__(self,fname):
    
    # CREATE OUTPUT FILE with single tree
    self.out = TreeProducer(fname,self)
    
    # ADD CUTS TO CUTFLOW
    self.out.cutflow.addcut('nocut',"No cut")
    self.out.cutflow.addcut('notop',"No top quarks in the event")
    
    # ADD HISTOGRAMS
    self.out.addHist('mass_lq',"LQ mass",2500,0,2500)
    self.out.addHist('dR_tj',"DeltaR between tau and closest jet",60,-1,5)
    self.out.addHist('dR_jt',"DeltaR between jet and closest tau",60,-1,5)
    self.out.addHist('dR_vt',"DeltaR between visible tau and closest tau",60,-1,5)
    
    # ADD BRANCHES
    self.out.addBranch('genweight',      'f', title="Generator weight")
    self.out.addBranch('nlqs',           'i', title="Number of LQs")
    self.out.addBranch('ntaus',          'i', title="Number of tau leptons")
    self.out.addBranch('nvistaus',       'i', title="Number of visible tau decay products (pT > 10 GeV)") # default cut
    self.out.addBranch('nvistaus20',     'i', title="Number of visible tau decay products (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('ntnus',          'i', title="Number of tau neutrinos")
    self.out.addBranch('nbots',          'i', title="Number of bottom quarks")
    self.out.addBranch('nbots20',        'i', title="Number of bottom quarks (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('ntops',          'i', title="Number of top quarks")
    self.out.addBranch('njets',          'i', title="Number of gen AK4 jets (no tau decays)")
    self.out.addBranch('nbjets',         'i', title="Number of gen AK4 b jets")
    self.out.addBranch('nbjets20',       'i', title="Number of gen AK4 b jets (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('nbjets50',       'i', title="Number of gen AK4 b jets (pT > 50 GeV, |eta|<2.5)")
    self.out.addBranch('ncjets20',       'i', title="Number of gen AK4 jets (pT > 20 GeV, |eta|<2.5)")
    self.out.addBranch('ncjets50',       'i', title="Number of gen AK4 jets (pT > 50 GeV, |eta|<2.5)")
    self.out.addBranch('nfjets20',       'i', title="Number of gen AK4 jets (pT > 20 GeV, 2.5<|eta|<4.7)")
    self.out.addBranch('nfjets50',       'i', title="Number of gen AK4 jets (pT > 50 GeV, 2.5<|eta|<4.7)")
    self.out.addBranch('dR_taus',        'f', title="DeltaR between tau leptons")
    self.out.addBranch('dR_vistaus',     'f', title="DeltaR between visible tau leptons")
    self.out.addBranch('dR_bots',        'f', title="DeltaR between bottom quarks")
    self.out.addBranch('mass_lq',        'f', title="LQ mass")
    self.out.addBranch('pt_lq1',         'f', title="pT of the leading LQ")
    self.out.addBranch('pt_lq2',         'f', title="pT of the subleading LQ") # for pair production only
    self.out.addBranch('dau1_lq1',       'i', title="PDG ID of daughter 1 of leading LQ")
    self.out.addBranch('dau1_lq2',       'i', title="PDG ID of daughter 2 of leading LQ")
    self.out.addBranch('dau2_lq1',       'i', title="PDG ID of daughter 1 of subleading LQ") # for pair production only
    self.out.addBranch('dau2_lq2',       'i', title="PDG ID of daughter 2 of subleading LQ") # for pair production only
    self.out.addBranch('pt_tau1',        'f', title="pT of leading tau")
    self.out.addBranch('pt_tau2',        'f', title="pT of subleading tau")
    self.out.addBranch('eta_tau1',       'f', title="eta of leading tau")
    self.out.addBranch('eta_tau2',       'f', title="eta of subleading tau")
    self.out.addBranch('moth_tau1',      'i', title="Mother of leading tau")
    self.out.addBranch('moth_tau2',      'i', title="Mother of subleading tau")
    self.out.addBranch('pt_vistau1',     'f', title="pT of leading tau")
    self.out.addBranch('pt_vistau2',     'f', title="pT of subleading vis. tau")
    self.out.addBranch('eta_vistau1',    'f', title="eta of leading tau")
    self.out.addBranch('eta_vistau2',    'f', title="eta of subleading vis. tau")
    self.out.addBranch('moth_vistau1',   'i', title="Mother of leading vis. tau")
    self.out.addBranch('moth_vistau2',   'i', title="Mother of subleading vis. tau")
    self.out.addBranch('pt_bot1',        'f', title="pT of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('pt_bot2',        'f', title="pT of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('eta_bot1',       'f', title="eta of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('eta_bot2',       'f', title="eta of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('moth_bot1',      'i', title="Mother of leading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('moth_bot2',      'i', title="Mother of subleading b quark (pT > 10 GeV, |eta|<4.7)")
    self.out.addBranch('pt_jet1',        'f', title="pT of leading gen jet")
    self.out.addBranch('pt_jet2',        'f', title="pT of subleading gen jet")
    self.out.addBranch('eta_jet1',       'f', title="eta of leading gen jet")
    self.out.addBranch('eta_jet2',       'f', title="eta of subleading gen jet")
    self.out.addBranch('flavor_jet1',    'i', title="flavor of leading gen jet")
    self.out.addBranch('flavor_jet2',    'i', title="flavor of subleading gen jet")
    self.out.addBranch('pt_bjet1',       'f', title="pT of leading gen b jet")
    self.out.addBranch('pt_bjet2',       'f', title="pT of subleading gen b jet")
    self.out.addBranch('eta_bjet1',      'f', title="eta of leading gen b jet")
    self.out.addBranch('eta_bjet2',      'f', title="eta of subleading gen b jet")
    
    # ADD ALIASES (to save disk space)
    self.out.setAlias('njets20', "nfjets20+ncjets20")
    self.out.setAlias('njets50', "nfjets50+ncjets50")
    
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('nocut')
    
    # PREPARE lists of selected gen-level particles
    taus    = [ ] # tau leptons
    jets    = [ ] # jets
    bjets   = [ ] # b jets
    cjets   = [ ] # central jets
    fjets   = [ ] # forward jets
    vistaus = [ ] # visible tau decay products (visible four-momentum)
    tnus    = [ ] # tau neutrinos
    bots    = [ ] # bottom quarks
    tops    = [ ] # top quarks
    lqs     = [ ] # LQs
    lqids   = [46,9000002,9000006] # PDG IDs of LQs in various MadGraph or Pythia generators
    
    # LOOP over gen-level particles
    #print '-'*80
    genparts = Collection(event,'GenPart') # generator-level particles
    genjets  = Collection(event,'GenJet') # generator-level jets
    for part in genparts:
      pid = abs(part.pdgId)
      #dumpgenpart(part,genparts=genparts) # print for debugging
      
      # LQ decay products
      for lq in lqs: # check if part is LQ decay product
        if lq._index==part.genPartIdxMother: # LQ is mother
          lq.decays.append(part.pdgId) # save PDG only
        
      # LAST COPY
      if not part.statusflag('isLastCopy'):
        continue # only analyze last copies
      
      # LQ particle
      if pid in lqids: # this particle is a LQ
        #if part.status<60:
        #  continue # about to decay (i.e. last copy)
        part.decays = [ ]
        lqs.append(part)
      
      # BOTTOM quark
      elif pid==5 and part.status!=21 and abs(part.eta)<10: # remove initial state b quark (from hard process)
        part.mother = getmother(part,genparts) # get mother PDG ID
        bots.append(part)
      
      # TOP quark
      elif pid==6:
        tops.append(part)
      
      # TAU lepton
      elif pid==15:
        part.mother = getmother(part,genparts) # get mother PDG ID
        taus.append(part)
        self.out.fill('dR_tj',getdRmin(part,genjets)) # DeltaR between tau and closest jet
      
      # TAU neutrinos
      elif pid==16:
        tnus.append(part)
    
    # VISIBLE TAUS (gen-level)
    # Because neutrinos carry away energy & momentum,
    # We need the four-momentum of the visible decay
    # products of the selected tau particles
    for vistau in Collection(event,'GenVisTau'):
      moth = None
      dRmin = 10
      for tau in taus: # gen-level taus
        dR = tau.DeltaR(vistau)
        if dR<dRmin: # match with "full" tau lepton
          dRmin = dR
          moth  = tau
      if dRmin<0.4: # found mother
        vistau.mother = moth.mother # PDG ID
      else: # did not find mother
        vistau.mother = 0  # default: 0 = no match found
      self.out.fill('dR_vt',dRmin) # DeltaR between visible tau and closest "full" tau lepton
      vistaus.append(vistau)
    
    # GEN AK4 JETS
    # All hadronic jets at gen-level
    for jet in genjets:
      dRmin_tau = getdRmin(jet,taus)
      self.out.fill('dR_jt',getdRmin(jet,taus)) # DeltaR between jet and closest tau
      if abs(jet.partonFlavour) in [0,15] and dRmin_tau<0.3:
        continue # remove overlap with taus
      jets.append(jet) # inclusive (except taus)
      if abs(jet.partonFlavour)==5: # b quark
        bjets.append(jet)
      if jet.pt>20:
        if abs(jet.eta)<2.5: # central jets (barrel)
          cjets.append(jet)
        elif abs(jet.eta)<4.7: # forward jets (endcaps)
          fjets.append(jet)
    
    #if len(ntops)>=1:
    #  return False # do not store event if it contains a top quark
    if len(tops)==0:
      self.out.cutflow.fill('notop')
    
    # FILL BRANCHES
    self.out.genweight[0]    = event.genWeight
    self.out.nlqs[0]         = len(lqs)
    self.out.nbots[0]        = len(bots)
    self.out.nbots20[0]      = sum([b.pt>20 and abs(b.eta)<2.5 for b in bots])
    self.out.ntops[0]        = len(tops)
    self.out.ntaus[0]        = len(taus)
    self.out.ntnus[0]        = len(tnus)
    self.out.nvistaus[0]     = len(vistaus)
    self.out.nvistaus20[0]   = sum([t.pt>20 and abs(t.eta)<2.5 for t in vistaus])
    self.out.njets[0]        = len(jets)
    self.out.nbjets[0]       = len(bjets)
    self.out.nbjets20[0]     = sum([j.pt>20 and abs(j.eta)<2.5 for j in bjets])
    self.out.nbjets50[0]     = sum([j.pt>50 and abs(j.eta)<2.5 for j in bjets])
    self.out.ncjets20[0]     = len(cjets)
    self.out.ncjets50[0]     = sum([j.pt>50 for j in cjets])
    self.out.nfjets20[0]     = len(fjets)
    self.out.nfjets50[0]     = sum([j.pt>50 for j in fjets])
    
    # FILL LQ BRANCHES
    if len(lqs)>=2: # LQ pair production
      lqs.sort(key=lambda lq: lq.pt,reverse=True) # sort LQ by pT
      lqs[0].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      lqs[1].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = lqs[1].pt
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = lqs[1].decays[0] if len(lqs[1].decays)>=1 else -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = lqs[1].decays[1] if len(lqs[1].decays)>=2 else -1
      self.out.mass_lq[0]  = lqs[0].p4().M() # get mass from TLorentzVector
    elif len(lqs)>=1: # single LQ production
      lqs[0].decays.sort(key=lambda p: abs(p)) # sort by PDG ID
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = -1
      self.out.mass_lq[0]  = lqs[0].p4().M() # get mass from TLorentzVector
    else: # nonres. production (LQ in the t-channel)
      self.out.pt_lq1[0]   = -1
      self.out.pt_lq2[0]   = -1
      self.out.dau1_lq1[0] = -1
      self.out.dau1_lq2[0] = -1
      self.out.dau2_lq1[0] = -1
      self.out.dau2_lq2[0] = -1
      self.out.mass_lq[0]  = -1
    
    # FILL TAU BRANCHES
    if len(taus)>=2:
      taus.sort(key=lambda t: t.pt,reverse=True) # sort taus by pT
      self.out.dR_taus[0]   = taus[0].DeltaR(taus[1])
      self.out.pt_tau1[0]   = taus[0].pt
      self.out.pt_tau2[0]   = taus[1].pt
      self.out.eta_tau1[0]  = taus[0].eta
      self.out.eta_tau2[0]  = taus[1].eta
      self.out.moth_tau1[0] = taus[0].mother
      self.out.moth_tau2[0] = taus[1].mother
    elif len(taus)>=1:
      self.out.dR_taus[0]   = -1
      self.out.pt_tau1[0]   = taus[0].pt
      self.out.pt_tau2[0]   = -1
      self.out.eta_tau1[0]  = taus[0].eta
      self.out.eta_tau2[0]  = -9
      self.out.moth_tau1[0] = taus[0].mother
      self.out.moth_tau2[0] = -1
    else: # no taus found
      self.out.dR_taus[0]   = -1
      self.out.pt_tau1[0]   = -1
      self.out.pt_tau2[0]   = -1
      self.out.eta_tau1[0]  = -9
      self.out.eta_tau2[0]  = -9
      self.out.moth_tau1[0] = -1
      self.out.moth_tau2[0] = -1
    
    # FILL VISIBLE TAU BRANCHES
    if len(vistaus)>=2:
      vistaus.sort(key=lambda t: t.pt,reverse=True) # sort taus by pT
      self.out.dR_vistaus[0]     = vistaus[0].DeltaR(vistaus[1])
      self.out.pt_vistau1[0]     = vistaus[0].pt
      self.out.pt_vistau2[0]     = vistaus[1].pt
      self.out.eta_vistau1[0]    = vistaus[0].eta
      self.out.eta_vistau2[0]    = vistaus[1].eta
      self.out.moth_vistau1[0]   = vistaus[0].mother
      self.out.moth_vistau2[0]   = vistaus[1].mother
    elif len(vistaus)>=1:
      self.out.dR_vistaus[0]     = -1
      self.out.pt_vistau1[0]     = vistaus[0].pt
      self.out.pt_vistau2[0]     = -1
      self.out.eta_vistau1[0]    = vistaus[0].eta
      self.out.eta_vistau2[0]    = -9
      self.out.moth_vistau1[0]   = vistaus[0].mother
      self.out.moth_vistau2[0]   = 0
    else: # no visible taus found
      self.out.dR_vistaus[0]     = -1
      self.out.pt_vistau1[0]     = -1
      self.out.pt_vistau2[0]     = -1
      self.out.eta_vistau1[0]    = -9
      self.out.eta_vistau2[0]    = -9
      self.out.moth_vistau1[0]   = 0
      self.out.moth_vistau2[0]   = 0
    self.out.fill() # fill branches
    
    # FILL BOTTOM QUARK BRANCHES
    if len(bots)>=2:
      bots.sort(key=lambda t: t.pt,reverse=True) # sort bottom quarks by pT
      self.out.dR_bots[0]   = bots[0].DeltaR(bots[1])
      self.out.pt_bot1[0]   = bots[0].pt
      self.out.pt_bot2[0]   = bots[1].pt
      self.out.eta_bot1[0]  = bots[0].eta
      self.out.eta_bot2[0]  = bots[1].eta
      self.out.moth_bot1[0] = bots[0].mother
      self.out.moth_bot2[0] = bots[1].mother
    elif len(bots)>=1:
      self.out.dR_bots[0]   = -1
      self.out.pt_bot1[0]   = bots[0].pt
      self.out.pt_bot2[0]   = -1
      self.out.eta_bot1[0]  = bots[0].eta
      self.out.eta_bot2[0]  = -9
      self.out.moth_bot1[0] = bots[0].mother
      self.out.moth_bot2[0] = -1
    else: # no bots found
      self.out.dR_bots[0]   = -1
      self.out.pt_bot1[0]   = -1
      self.out.pt_bot2[0]   = -1
      self.out.eta_bot1[0]  = -9
      self.out.eta_bot2[0]  = -9
      self.out.moth_bot1[0] = -1
      self.out.moth_bot2[0] = -1
    
    # FILL JET BRANCHES
    if len(jets)>=2:
      jets.sort(key=lambda j: j.pt,reverse=True) # sort jets by pT
      self.out.pt_jet1[0]     = jets[0].pt
      self.out.pt_jet2[0]     = jets[1].pt
      self.out.eta_jet1[0]    = jets[0].eta
      self.out.eta_jet2[0]    = jets[1].eta
      self.out.flavor_jet1[0] = jets[0].partonFlavour
      self.out.flavor_jet2[0] = jets[1].partonFlavour
    elif len(jets)>=1:
      self.out.pt_jet1[0]     = jets[0].pt
      self.out.pt_jet2[0]     = -1
      self.out.eta_jet1[0]    = jets[0].eta
      self.out.eta_jet2[0]    = -9
      self.out.flavor_jet1[0] = jets[0].partonFlavour
      self.out.flavor_jet2[0] = 0
    else: # no jets found
      self.out.pt_jet1[0]     = -1
      self.out.pt_jet2[0]     = -1
      self.out.eta_jet1[0]    = -9
      self.out.eta_jet2[0]    = -9
      self.out.flavor_jet1[0] = 0
      self.out.flavor_jet2[0] = 0
    
    # FILL B JET BRANCHES
    if len(bjets)>=2:
      bjets.sort(key=lambda j: j.pt,reverse=True) # sort b jets by pT
      self.out.pt_bjet1[0]  = bjets[0].pt
      self.out.pt_bjet2[0]  = bjets[1].pt
      self.out.eta_bjet1[0] = bjets[0].eta
      self.out.eta_bjet2[0] = bjets[1].eta
    elif len(bjets)>=1:
      self.out.pt_bjet1[0]  = bjets[0].pt
      self.out.pt_bjet2[0]  = -1
      self.out.eta_bjet1[0] = bjets[0].eta
      self.out.eta_bjet2[0] = -9
    else: # no b jets found
      self.out.pt_bjet1[0]  = -1
      self.out.pt_bjet2[0]  = -1
      self.out.eta_bjet1[0] = -9
      self.out.eta_bjet2[0] = -9
    
    # FILL HISTOGRAMS
    for lq in lqs:
      mass = lq.p4().M() # get mass from TLorentzVector
      self.out.fill('mass_lq',mass)
    
    return True
  

# QUICK PLOTTING SCRIPT
if __name__ == '__main__':
  
  # USER OPTIONS
  from argparse import ArgumentParser
  parser = ArgumentParser()
  parser.add_argument('-i',   '--infiles', nargs='+')
  parser.add_argument('-o',   '--outdir', default='.')
  parser.add_argument('-tag', '--tag', default='', help="extra tag for name of output file")
  parser.add_argument('-n',   '--maxevts', type=int, default=10000)
  parser.add_argument('-L',   '--lq', choices=['s','p','t','x'], default='t',
                                      help="select pre-defined list of input files for pair ('p'), single ('s'), or nonres. ('t')")
  args = parser.parse_args()
  
  # SETTINGS
  maxevts = args.maxevts if args.maxevts>0 else None
  outfname = "genAnalyzer_LQ%s.root"%(args.tag)
  modules = [ModuleGenLQ(outfname)]
  
  # INPUT FILES
  url = "root://cms-xrd-global.cern.ch/"
  indir = "/eos/user/i/ineuteli/public/forCalTech/NANOAOD/"
  if args.infiles:
    infiles = args.infiles
  elif args.lq=='p': # LQ pair production
    # for d in /eos/user/i/ineuteli/public/forCalTech/NANOAOD/*1400*/*/*; do ls $d/*root | head; done
    infiles = [
      indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_100_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_101_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_102_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_103_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_104_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_106_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_107_skimmed_JECSys.root",
      #indir+"/PairVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_108_skimmed_JECSys.root",
    ]
  elif args.lq=='s': # single LQ production
    infiles = [
      indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_100_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_101_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_102_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_103_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_104_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_105_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_106_skimmed_JECSys.root",
      #indir+"/SingleVectorLQ_InclusiveDecay_M-1400_TuneCP2_13TeV-madgraph-pythia8/ineuteli-RunIIAutumn18NanoAODv6_102X_upgrade2018_realistic_v20-46cdbfd14e9c61da1d6c94f005ec4720/USER/nanoAOD_2018_107_skimmed_JECSys.root",
    ]
  elif args.lq=='t': # nonresonant production
    infiles = [
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_0_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_10_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_11_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_12_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_100_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_101_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_102_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_103_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_104_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_105_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_106_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_107_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_108_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_109_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_110_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_111_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_112_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_113_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_114_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_115_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_116_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_117_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_118_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_119_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_120_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_121_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_122_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_123_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_124_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_125_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_126_skimmed_JECSys.root",
    ]
  else:
    infiles = [
      #url+'/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/280000/525CD279-3344-6043-98B9-2EA8A96623E4.root',
      url+'/store/mc/RunIISummer20UL18NanoAODv9/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/130000/44187D37-0301-3942-A6F7-C723E9F4813D.root',
    ]
  
  # PROCESS NANOAOD
  processor = PostProcessor(args.outdir,infiles,noOut=True,modules=modules,maxEntries=maxevts)
  processor.run()
  
