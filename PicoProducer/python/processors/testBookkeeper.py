#! /usr/bin/env python
# Author: Izaak Neutelings (July 2022)
# Description: Test Bookkeeper module
# Instructions:
#   python/processors/testBookkeeper.py -v2 -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_[01].root
#   python/processors/testBookkeeper.py -v2 --preselect 'nMuon>0 && Muon_pt>20' -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_[01].root
#   python/processors/testBookkeeper.py -v2 -m 1000 -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_[01].root
#   python/processors/testBookkeeper.py -v2 -m 1000 --preselect 'nMuon>0 && Muon_pt>20' -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_[01].root
#   python/processors/testBookkeeper.py -v2 -s 197000 -m 2000 -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_0.root
#   python/processors/testBookkeeper.py -v2 -s 197000 -m 2000 --preselect 'nMuon>0 && Muon_pt>20' -i /eos/cms/store/group/phys_tau/TauFW/nano/UL2018/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/A02A0DD5-3BFA-D742-80BA-AEF49B78A237_skimjec_0.root0CF0CDED-7582-7A49-84CD-0E5F73DE27B0_skimjec.root
from __future__ import print_function # for python3 compatibility
import os, glob
import time; time0 = time.time()
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from TauFW.PicoProducer.processors import moddir, ensuredir
from TauFW.common.tools.utils import getyear
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles', dest='infiles',   default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',  dest='outdir',    default='output')
parser.add_argument('--preselect',     dest='preselect', default=None)
parser.add_argument('-s', '--firstevt',dest='firstevt',  type=int, default=0)
parser.add_argument('-m', '--maxevts', dest='maxevts',   type=int, default=None)
parser.add_argument('-t', '--tag',     dest='tag',       default="testBookkeeper")
parser.add_argument('-p', '--prefetch',dest='prefetch',  action='store_true')
parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0,
                                       help="set verbosity" )
args = parser.parse_args()


# SETTING
outdir    = ensuredir(args.outdir)  # directory to create output
firstevt  = args.firstevt           # index of first event to run
maxevts   = args.maxevts            # maximum number of events to run
nfiles    = -1 if maxevts>0 else -1 # maximum number of files to run
prefetch  = args.prefetch          # copy input file(s) to ouput directory first
presel    = args.preselect         # simple pre-selection string, e.g. for mutau: "HLT_IsoMu27 && Muon_pt>28 && Tau_pt>18"
branchsel = os.path.join(moddir,"keep_and_drop_skim.txt") # file with branch selection
json      = None                   # JSON file of certified events
modules   = [ ]                    # list of modules to run
verbosity = args.verbosity         # verbosity level
tag       = args.tag               # postfix tag of job output file

# TAG
tag = ('' if not tag or tag.startswith('_') else '_') + tag
tag += "_evt-%s-%s"%(firstevt,firstevt+maxevts if maxevts else 'max')
if presel:
  tag += "_presel"

# INPUT FILES
url = "root://cms-xrd-global.cern.ch/"
infiles = args.infiles or [ # for testing
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/C9EAE9C3-7392-6B48-8FD2-A2DCA1C6B2C7.root",
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/04BBC240-E6D5-824C-9688-835C8D1D9C12.root",
]
if nfiles>0:
  infiles = infiles[:nfiles]

# SIMPLE MODULE FOR TESTING CUTFLOW
class ModuleMuTau(Module):
  def analyze(self,event):
    #ntaus = sum(event.Tau_pt[i]>20 and abs(event.Tau_eta[i])<2.5 and ord(event.Tau_idDeepTau2017v2p1VSjet[i])>=8 for i in range(event.nTau))
    #nmouns = sum(event.Muon_pt[i]>24 and abs(event.Muon_eta[i])<2.5 for i in range(event.nMuon))
    taus = [t for t in Collection(event,'Tau') if t.pt>20 and abs(t.eta)<2.5 and t.idDeepTau2017v2p1VSjet>=4 and t.idDeepTau2017v2p1VSmu>=1]
    if len(taus)==0: return
    mouns = [m for m in Collection(event,'Muon') if m.pt>24 and abs(m.eta)<2.5 and any(m.DeltaR(t)>0.5 for t in taus)]
    return len(mouns)>=1
modules.append(ModuleMuTau())

# BOOKKEEPING
from TauFW.PicoProducer.processors.Bookkeeper import Bookkeeper
modules.append(Bookkeeper(verb=verbosity)) # order should not matter

# PRINT
print('-'*80)
print(">>> %-12s = %s"%('firstevt',firstevt))
print(">>> %-12s = %s"%('maxevts',maxevts))
print(">>> %-12s = %r"%('tag',tag))
print(">>> %-12s = %r"%('outdir',outdir))
print(">>> %-12s = %s"%('infiles',infiles))
print(">>> %-12s = %r"%('branchsel',branchsel))
print(">>> %-12s = %r"%('json',json))
print(">>> %-12s = %s"%('modules',modules))
print(">>> %-12s = %s"%('prefetch',prefetch))
print(">>> %-12s = %r"%('cwd',os.getcwd()))
print(">>> %-12s = %r"%('preselection',presel))
print('-'*80)

# RUN
print(">>> Loading post processor...")
p = PostProcessor(outdir,infiles,cut=presel,branchsel=None,outputbranchsel=branchsel,
                  firstEntry=firstevt,maxEntries=maxevts,jsonInput=json,
                  modules=modules,postfix=tag,noOut=False,prefetch=prefetch)
print(">>> Start post processor...")
p.run()
print(">>> Finished post processor...")
print('-'*80)

# DONE
print(">>> skimjob.py done after %.1f seconds"%(time.time()-time0))
