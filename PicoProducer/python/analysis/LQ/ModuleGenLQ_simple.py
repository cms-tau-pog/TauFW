#! /usr/bin/env python3
# Author: Izaak Neutelings (June 2020)
# Description:
#   Simple example of gen-level study of LQ samples.
#   This analysis module selects interesting particles for various LQ processes,
#   and creates an output file with a single flat tree for several kinematic variables.
# Sources:
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-106X/mc106Xul18_doc.html#GenPart
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/genparticles_cff.py
#   https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/LHETablesProducer.cc
#   https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/examples/exampleGenDump.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/GenDumper.py
#   https://github.com/cms-tau-pog/TauFW/blob/master/PicoProducer/python/analysis/LQ/ModuleGenLQ.py
from __future__ import print_function # for python3 compatibility
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
#import PhysicsTools.NanoAODTools.postprocessing.framework.datamodel as datamodel
#from TauFW.PicoProducer.analysis.utils import dumpgenpart
#datamodel.statusflags['isHardPrompt'] = datamodel.statusflags['isPrompt'] + datamodel.statusflags['fromHardProcess'] 


# DUMPER MODULE
class ModuleGenLQ(Module):
  
  def __init__(self,fname):
    
    # CREATE OUTPUT FILE with single tree
    self.out = TreeProducer(fname,self)
    
    # ADD CUTS TO CUTFLOW
    self.out.cutflow.addcut('nocut',"No cut")
    self.out.cutflow.addcut('notop',"No top quarks in the event")
    
    # ADD BRANCHES
    self.out.addBranch('genweight',    'f', title="Generator weight")
    self.out.addBranch('nlqs',         'i', title="Number of LQs")
    self.out.addBranch('ntaus',        'i', title="Number of tau leptons")
    self.out.addBranch('nvistaus',     'i', title="Number of visible tau decay products")
    self.out.addBranch('ntnus',        'i', title="Number of tau neutrinos")
    self.out.addBranch('ntops',        'i', title="Number of top quarks")
    self.out.addBranch('dr_taus',      'f', title="DeltaR between tau leptons")
    self.out.addBranch('dr_vistaus',   'f', title="DeltaR between visible tau leptons")
    self.out.addBranch('mass_lq',      'f', title="LQ mass")
    self.out.addBranch('pt_lq1',       'f', title="pT of the leading LQ")
    self.out.addBranch('pt_lq2',       'f', title="pT of the subleading LQ") # for pair production only
    self.out.addBranch('dau1_lq1',     'f', title="PDG ID of daughter 1 of leading LQ")
    self.out.addBranch('dau1_lq2',     'f', title="PDG ID of daughter 2 of leading LQ")
    self.out.addBranch('dau2_lq1',     'f', title="PDG ID of daughter 1 of subleading LQ") # for pair production only
    self.out.addBranch('dau2_lq2',     'f', title="PDG ID of daughter 2 of subleading LQ") # for pair production only
    self.out.addBranch('pt_vistau1',   'f', title="pT of leading vis. tau")
    self.out.addBranch('pt_vistau2',   'f', title="pT of subleading vis. tau")
    self.out.addBranch('moth_vistau1', 'f', title="Mother of leading vis. tau")
    self.out.addBranch('moth_vistau2', 'f', title="Mother of subleading vis. tau")
    
    # ADD HISTOGRAMS
    self.out.addHist("mass_lq","LQ mass",2500,0,2500)
    
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.out.endJob()
  
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    self.out.cutflow.fill('nocut')
    
    # PREPARE lists of selected gen-level particles
    taus    = [ ] # tau leptons
    vistaus = [ ] # visible tau decay products (visible four-momentum)
    tnus    = [ ] # tau neutrinos
    tops    = [ ] # top quarks
    lqs     = [ ] # LQs
    lqids   = [46,9000002,9000006] # PDG IDs of LQs in various MadGraph or Pythia generators
    
    # LOOP over gen-level particles
    #print '-'*80
    genparts = Collection(event,'GenPart') # generator-level particles
    for part in genparts:
      pid = abs(part.pdgId)
      #dumpgenpart(part,genparts=genparts) # print for debugging
      
      # LQ particle
      if pid in lqids: # this particle is a LQ
        if part.status<60: continue # about to decay (i.e. last copy)
        for i, lq in enumerate(lqs):
          if lq._index==part.genPartIdxMother and lq.pdgId==part.pdgId:
            lqs[i] = part # replace previous top with last copy
            break
        else:
          part.decays = [ ]
          lqs.append(part)
      
      # non-LQ particle
      else:
        for lq in lqs: # check if part is LQ decay product
          if lq._index==part.genPartIdxMother: # LQ is mother
            lq.decays.append(pid) # save PDG only
        
        # TOP quark
        if pid==6:
          for i, top in enumerate(tops):
            if top._index==part.genPartIdxMother and top.pdgId==part.pdgId: # last copy
              tops[i] = part # replace previous top with last copy
              break
          else:
            tops.append(part)
        
        # TAU lepton
        elif pid==15:
          for i, tau in enumerate(taus):
            if tau._index==part.genPartIdxMother and tau.pdgId==part.pdgId:
              taus[i] = part # replace previous tau with last copy
              break
          else:
            taus.append(part)
        elif pid==16:
          tnus.append(part)
    
    # VISIBLE TAUS (gen-level)
    # Because neutrinos carry away energy & momentum,
    # We need the four-momentum of the visible decay
    # products of the selected tau particles
    for vistau in Collection(event,'GenVisTau'):
      vistau.mother = -1
      for tau in taus: # gen-level taus
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
    
    #if len(ntops)>=1:
    #  return False # do not store event if it contains a top quark
    if len(tops)==0:
      self.out.cutflow.fill('notop')
    
    # FILL BRANCHES to store branches
    self.out.genweight[0]  = event.genWeight
    self.out.nlqs[0]       = len(lqs)
    self.out.ntaus[0]      = len(taus)
    self.out.ntnus[0]      = len(tnus)
    self.out.nvistaus[0]   = len(vistaus)
    self.out.ntops[0]      = len(tops)
    if len(lqs)>=2: # LQ pair production
      lqs.sort(key=lambda lq: lq.pt,reverse=True) # sort LQ by pT
      lqs[0].decays.sort() # sort by PDG ID
      lqs[1].decays.sort() # sort by PDG ID
      self.out.pt_lq1[0]   = lqs[0].pt
      self.out.pt_lq2[0]   = lqs[1].pt
      self.out.dau1_lq1[0] = lqs[0].decays[0] if len(lqs[0].decays)>=1 else -1
      self.out.dau1_lq2[0] = lqs[1].decays[0] if len(lqs[1].decays)>=1 else -1
      self.out.dau2_lq1[0] = lqs[0].decays[1] if len(lqs[0].decays)>=2 else -1
      self.out.dau2_lq2[0] = lqs[1].decays[1] if len(lqs[1].decays)>=2 else -1
      self.out.mass_lq[0]  = lqs[0].p4().M() # get mass from TLorentzVector
    elif len(lqs)>=1: # single LQ production
      lqs[0].decays.sort() # sort by PDG ID
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
    if len(taus)>=2:
      taus.sort(key=lambda t: t.pt,reverse=True) # sort taus by pT
      self.out.dr_taus[0]  = taus[0].DeltaR(taus[1])
    if len(vistaus)>=2:
      vistaus.sort(key=lambda t: t.pt,reverse=True) # sort taus by pT
      self.out.dr_vistaus[0]  = vistaus[0].DeltaR(vistaus[1])
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
    self.out.fill() # fill branches
    
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
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_100_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_101_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_102_skimmed_JECSys.root",
      indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_103_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_104_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_105_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_106_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_107_skimmed_JECSys.root",
      #indir+"/LQ_VecNonRes_M1400/LegacyRun2_2018_deepTauIDv2p1/USER/nanoAOD_LegacyRun2_2018_deepTauIDv2p1_test_LQ_VecNonRes_5f_Madgraph_LO_M1400_108_skimmed_JECSys.root",
    ]
  else:
    infiles = [
      url+'/store/mc/RunIISummer20UL18NanoAODv9/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/280000/525CD279-3344-6043-98B9-2EA8A96623E4.root',
      #url+'/store/mc/RunIISummer20UL18NanoAODv9/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/130000/44187D37-0301-3942-A6F7-C723E9F4813D.root',
    ]
  
  # PROCESS NANOAOD
  processor = PostProcessor(args.outdir,infiles,noOut=True,modules=modules,maxEntries=maxevts)
  processor.run()
  
