#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Skim
import os
import time; time0 = time.time()
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from TauFW.PicoProducer.processors import moddir
from TauFW.PicoProducer.corrections.era_config import getjson, getera, getjmecalib
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles',  dest='infiles',  type=str, default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',   dest='outdir',   type=str, default='.')
parser.add_argument('-C', '--copydir',  dest='copydir',  type=str, default='.')
parser.add_argument('-n', '--Nmax',     dest='maxevts',  type=int, default=100)
parser.add_argument('-t', '--tag',      dest='tag',      type=str, default="")
parser.add_argument('-d', '--dtype',    dest='dtype',    choices=['data','mc','embed'], default=None)
parser.add_argument('-y', '--year',     dest='year',     choices=[2016,2017,2018], type=int, default=2018)
parser.add_argument('-e', '--era',      dest='era',      type=str, default="")
parser.add_argument('-p', '--prefetch', dest='prefetch', action='store_true', default=False)
parser.add_argument('-J', '--jec',      dest='doJEC',     action='store_true', default=False)
parser.add_argument('-S', '--jec-sys',  dest='doJECSys',  action='store_true', default=False)
args = parser.parse_args()


# SETTING
year      = args.year
era       = args.era
dtype     = args.dtype
outdir    = args.outdir
copydir   = args.copydir
maxevts   = args.maxevts if args.maxevts>0 else None
nfiles    = -1
tag       = args.tag
tag       = ('' if not tag or tag.startswith('_') else '_') + tag
postfix   = "_skimmed"+tag
director  = "root://cms-xrd-global.cern.ch/"
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
  director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/67/myNanoProdMc2017_NANO_66.root',
  director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/68/myNanoProdMc2017_NANO_67.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/69/myNanoProdMc2017_NANO_68.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/70/myNanoProdMc2017_NANO_69.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/71/myNanoProdMc2017_NANO_70.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/72/myNanoProdMc2017_NANO_71.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/73/myNanoProdMc2017_NANO_72.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/74/myNanoProdMc2017_NANO_73.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/75/myNanoProdMc2017_NANO_74.root',
  #director+'/store/user/aakhmets/taupog/nanoAOD/DYJetsToLLM50_RunIIFall17MiniAODv2_PU2017RECOSIMstep_13TeV_MINIAOD_madgraph-pythia8_v1/76/myNanoProdMc2017_NANO_75.root',
]
if nfiles>0:
  infiles = infiles[:nfiles]
if dtype==None:
  dtype = 'mc'
if any(s in infiles[0] for s in ['SingleMuon',"/Tau/",'SingleElectron','EGamma']):
  dtype = 'data'

if dtype=='data':
  if not era:
    era = getera(filename,year,dtype=dtype)
  json  = getjson(dtype)
else:
  jmecalib = getjmecalib(year,era="",redoJEC=doJEC,doSys=doJECSys,dtype='mc')
  modules.append(jmecalib)

# PRINT
print '-'*80
print ">>> %-12s = %s"%('year',year)
print ">>> %-12s = %r"%('era',era)
print ">>> %-12s = %r"%('dtype',dtype)
print ">>> %-12s = %s"%('maxevts',maxevts)
print ">>> %-12s = %s"%('outdir',outdir)
print ">>> %-12s = %r"%('postfix',postfix)
print ">>> %-12s = %s"%('infiles',infiles)
print ">>> %-12s = %s"%('branchsel',branchsel)
print ">>> %-12s = %r"%('json',json)
print ">>> %-12s = %s"%('modules',modules)
print ">>> %-12s = %s"%('prefetch',prefetch)
print ">>> %-12s = %s"%('doJEC',doJEC)
print ">>> %-12s = %s"%('doJECSys',doJECSys)
print '-'*80

# RUN
p = PostProcessor(outdir,infiles,cut=None,branchsel=None,outputbranchsel=branchsel,noOut=False,
                  modules=modules,jsonInput=json,postfix=postfix,maxEntries=maxevts,prefetch=prefetch)
p.run()

# COPY
if copydir:
  from TauFW.PicoProducer.storage.StorageSystem import getstorage
  store = getstorage(copydir,verb=2)
  outfiles = os.path.join(outdir,"*%s.root"%postfix)
  store.cp(outfiles)

# DONE
print ">>> Done after %.1f seconds"%(time.time()-time0)
