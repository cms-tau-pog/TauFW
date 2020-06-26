#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Skim
import os
import time; time0 = time.time()
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from TauFW.PicoProducer.processors import moddir
from TauFW.PicoProducer.corrections.era_config import getjson, getera, getjmecalib
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles',  dest='infiles',  type=str, default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',   dest='outdir',   type=str, default='.')
parser.add_argument('-C', '--copydir',  dest='copydir',  type=str, default=None)
parser.add_argument('-m', '--maxevts',  dest='maxevts',  type=int, default=-1)
parser.add_argument('-t', '--tag',      dest='tag',      type=str, default="")
parser.add_argument('-d', '--dtype',    dest='dtype',    choices=['data','mc','embed'], default=None)
parser.add_argument('-y','-e','--era',  dest='era',      type=str, default="")
parser.add_argument('-p', '--prefetch', dest='prefetch', action='store_true', default=False)
parser.add_argument('-J', '--jec',      dest='doJEC',     action='store_true', default=False)
parser.add_argument('-S', '--jec-sys',  dest='doJECSys',  action='store_true', default=False)
args = parser.parse_args()


# SETTING
era       = args.era
dtype     = args.dtype
outdir    = args.outdir
copydir   = args.copydir
maxevts   = args.maxevts if args.maxevts>0 else None
nfiles    = -1 if maxevts>0 else -1
tag       = args.tag
tag       = ('' if not tag or tag.startswith('_') else '_') + tag
postfix   = tag
url       = "root://cms-xrd-global.cern.ch/"
prefetch  = args.prefetch
doJEC     = args.doJEC #and dataType=='data'
doJECSys  = args.doJECSys
presel    = None #"Muon_pt[0] > 50"
branchsel = os.path.join(moddir,"keep_and_drop_skim.txt")
json      = None
modules   = [ ]
infiles   = args.infiles or [
  #"data/DYJetsToLL_M-50_NanoAODv6.root",
  #"/afs/cern.ch/user/i/ineuteli/analysis/CMSSW_10_3_3/src/TauFW/PicoProducer/data/DYJetsToLL_M-50_NanoAODv6.root",
  url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/67/myNanoProdMc2017_NANO_66.root',
  url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/68/myNanoProdMc2017_NANO_67.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/69/myNanoProdMc2017_NANO_68.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/70/myNanoProdMc2017_NANO_69.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/71/myNanoProdMc2017_NANO_70.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/72/myNanoProdMc2017_NANO_71.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/73/myNanoProdMc2017_NANO_72.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/74/myNanoProdMc2017_NANO_73.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/75/myNanoProdMc2017_NANO_74.root',
  #url+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/76/myNanoProdMc2017_NANO_75.root',
]
if nfiles>0:
  infiles = infiles[:nfiles]
if dtype==None:
  if any(s in infiles[0] for s in ['SingleMuon',"/Tau/",'SingleElectron','EGamma']):
    dtype = 'data'
  else:
    dtype = 'mc'

if dtype=='data':
  if not era:
    era = getera(infiles[0],era,dtype=dtype) # gets data run (e.g. '2016B') from filename
  assert all(era in f for f in infiles), "Not all files names are of the same era '%s': %s"%(era,infiles)
  json  = getjson(era,dtype)
else:
  jmecalib = getjmecalib(era,era="",redoJEC=doJEC,doSys=doJECSys,dtype='mc')
  modules.append(jmecalib)

# PRINT
print '-'*80
print ">>> %-12s = %r"%('era',era)
print ">>> %-12s = %r"%('dtype',dtype)
print ">>> %-12s = %s"%('maxevts',maxevts)
print ">>> %-12s = %r"%('outdir',outdir)
print ">>> %-12s = %r"%('copydir',copydir)
print ">>> %-12s = %r"%('postfix',postfix)
print ">>> %-12s = %s"%('infiles',infiles)
print ">>> %-12s = %r"%('branchsel',branchsel)
print ">>> %-12s = %r"%('json',json)
print ">>> %-12s = %s"%('modules',modules)
print ">>> %-12s = %s"%('prefetch',prefetch)
print ">>> %-12s = %s"%('doJEC',doJEC)
print ">>> %-12s = %s"%('doJECSys',doJECSys)
print ">>> %-12s = %s"%('cwd',os.getcwd())
print '-'*80

# RUN
p = PostProcessor(outdir,infiles,cut=None,branchsel=None,outputbranchsel=branchsel,noOut=False,
                  modules=modules,jsonInput=json,postfix=postfix,maxEntries=maxevts,prefetch=prefetch)
p.run()

# COPY
if copydir and outdir!=copydir:
  from TauFW.PicoProducer.storage.utils import getstorage
  from TauFW.common.tools.file import rmfile
  store = getstorage(copydir,verb=2)
  outfiles = os.path.join(outdir,"*%s.root"%postfix)
  store.cp(outfiles)
  print ">>> Removing %s..."%(outfiles)
  rmfile(outfiles)

# DONE
print ">>> skimjob.py done after %.1f seconds"%(time.time()-time0)
