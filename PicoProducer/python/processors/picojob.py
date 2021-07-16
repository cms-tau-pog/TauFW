#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Skim nanoAOD file and store locally: pre-select events, filter branches, add jet/MET corrections, ...
from __future__ import print_function
import os, re
import time; time0 = time.time()
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from TauFW.PicoProducer.analysis.utils import getmodule, getyear, convertstr
from TauFW.PicoProducer.processors import moddir, ensuredir
from TauFW.PicoProducer.corrections.era_config import getjson
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles',  dest='infiles',   type=str, default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',   dest='outdir',    type=str, default='.')
parser.add_argument('-C', '--copydir',  dest='copydir',   type=str, default=None)
parser.add_argument('-s', '--firstevt', dest='firstevt',  type=int, default=0)
parser.add_argument('-m', '--maxevts',  dest='maxevts',   type=int, default=None)
parser.add_argument('-t', '--tag',      dest='tag',       type=str, default="")
parser.add_argument('-d', '--dtype',    dest='dtype',     choices=['data','mc','embed'], default=None)
parser.add_argument('-y','-e','--era',  dest='era',       type=str, default='2018')
parser.add_argument('-M', '--module',   dest='module',    type=str, default=None)
parser.add_argument('-c', '--channel',  dest='channel',   type=str, default=None)
parser.add_argument('-E', '--opts',     dest='extraopts', type=str, default=[ ], nargs='+')
parser.add_argument('-p', '--prefetch', dest='prefetch',  action='store_true', default=False)
parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0, action='store' )
args = parser.parse_args()


# SETTING
era       = args.era      # e.g. '2017', 'UL2017', ...
year      = getyear(era)  # integer year, e.g. 2017
modname   = args.module   # main module to run
channel   = args.channel  # channel
if channel:
  import TauFW.PicoProducer.tools.config as GLOB
  CONFIG  = GLOB.getconfig(verb=0)
  if not modname:
    assert channel in CONFIG.channels, "Did not find channel '%s' in configuration. Available channels: %s"%(channel,CONFIG.channels)
    modname = CONFIG.channels[args.channel]
else:
  if not modname:
    modname = "ModuleMuTauSimple"
  channel = modname
dtype     = args.dtype             # data type ('data', 'mc', 'embed')
outdir    = ensuredir(args.outdir) # directory to create output
copydir   = args.copydir           # directory to copy output to at end
firstevt  = args.firstevt          # index of first event to run
maxevts   = args.maxevts           # maximum number of events to run
nfiles    = 1 if maxevts>0 else -1 # maximum number of files to run
tag       = args.tag               # postfix tag of job output file
if tag:
  tag     = ('' if tag.startswith('_') else '_') + tag
outfname  = os.path.join(outdir,"pico%s.root"%(tag)) #channel,
url       = "root://cms-xrd-global.cern.ch/"
prefetch  = args.prefetch          # copy input file(s) to ouput directory first
verbosity = args.verbosity         # verbosity level
presel    = None                   # simple pre-selection string, e.g. "Muon_pt[0] > 50"
branchsel = os.path.join(moddir,"keep_and_drop_skim.txt") # file with branch selection
json      = None                   # JSON file of certified events
modules   = [ ]                    # list of modules to run

# GET FILES
infiles   = args.infiles or [
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/C9EAE9C3-7392-6B48-8FD2-A2DCA1C6B2C7.root",
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/04BBC240-E6D5-824C-9688-835C8D1D9C12.root",
  #"root://eosuser.cern.ch//eos/cms/store/group/phys_tau/TauFW/nano/UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/C9EAE9C3-7392-6B48-8FD2-A2DCA1C6B2C7_skimjec_0.root",
  #"root://eosuser.cern.ch//eos/cms/store/group/phys_tau/TauFW/nano/UL2018/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM/C9EAE9C3-7392-6B48-8FD2-A2DCA1C6B2C7_skimjec_1.root",
]
if nfiles>0:
  infiles = infiles[:nfiles]
if dtype==None:
  if any(s in infiles[0] for s in ['SingleMuon',"/Tau/",'SingleElectron','EGamma']):
    dtype = 'data'
  else:
    dtype = 'mc'
if dtype=='data':
  json = getjson(era,dtype)

# EXTRA OPTIONS
kwargs = { 'era': era, 'year': year, 'dtype': dtype, 'verb': verbosity }
for option in args.extraopts:
  assert '=' in option, "Extra option '%s' should contain '='! All: %s"%(option,args.extraopts)
  split       = option.split('=')
  key, val    = split[0], ''.join(split[1:])
  kwargs[key] = convertstr(val) # convert to bool, float or int if possible

# PRINT
print('-'*80)
print(">>> %-12s = %r"%('era',era))
print(">>> %-12s = %r"%('year',year))
print(">>> %-12s = %r"%('channel',channel))
print(">>> %-12s = %r"%('modname',modname))
print(">>> %-12s = %r"%('dtype',dtype))
print(">>> %-12s = %r"%('kwargs',kwargs))
print(">>> %-12s = %s"%('firstevt',firstevt))
print(">>> %-12s = %s"%('maxevts',maxevts))
print(">>> %-12s = %r"%('outdir',outdir))
print(">>> %-12s = %r"%('copydir',copydir))
print(">>> %-12s = %s"%('infiles',infiles))
print(">>> %-12s = %r"%('outfname',outfname))
print(">>> %-12s = %r"%('branchsel',branchsel))
print(">>> %-12s = %r"%('json',json))
print(">>> %-12s = %s"%('prefetch',prefetch))
print(">>> %-12s = %s"%('cwd',os.getcwd()))
print('-'*80)

# GET MODULE
module = getmodule(modname)(outfname,**kwargs)
modules.append(module)

# RUN
p = PostProcessor(outdir,infiles,cut=None,branchsel=None,firstEntry=firstevt,maxEntries=maxevts,
                  jsonInput=json,modules=modules,noOut=True,prefetch=prefetch)
p.run()

# COPY
if copydir and outdir!=copydir:
  print(">>> %-12s = %s"%('cwd',os.getcwd()))
  print(">>> %-12s = %s"%('ls',os.listdir(outdir)))
  from TauFW.PicoProducer.storage.utils import getstorage
  from TauFW.common.tools.file import rmfile
  store = getstorage(copydir,verb=2)
  store.cp(outfname)
  print(">>> Removing %r..."%(outfname))
  rmfile(outfname)

# DONE
print(">>> picojob.py done after %.1f seconds"%(time.time()-time0))
