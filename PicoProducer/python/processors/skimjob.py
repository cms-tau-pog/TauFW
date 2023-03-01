#! /usr/bin/env python
# Author: Izaak Neutelings (May 2020)
# Description: Skim & apply JME corrections
from __future__ import print_function # for python3 compatibility
import os, glob
import time; time0 = time.time()
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import createJMECorrector as getjmecalib
from TauFW.PicoProducer.processors import moddir, ensuredir
from TauFW.PicoProducer.corrections.era_config import getjson, getperiod #, getjmecalib
from TauFW.common.tools.utils import getyear
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-i', '--infiles',   dest='infiles',   default=[ ], nargs='+')
parser.add_argument('-o', '--outdir',    dest='outdir',    default='.')
parser.add_argument('-C', '--copydir',   dest='copydir',   default=None)
parser.add_argument('--preselect',       dest='preselect', default=None)
parser.add_argument('--common-presel',   dest='commonpresel', action='store_true')
parser.add_argument('-s', '--firstevt',  dest='firstevt',  type=int, default=0)
parser.add_argument('-m', '--maxevts',   dest='maxevts',   type=int, default=None)
parser.add_argument('-t', '--tag',       dest='tag',       default="skim")
parser.add_argument('-d', '--dtype',     dest='dtype',     choices=['data','mc','embed'], default=None)
parser.add_argument('-y', '-e','--era',  dest='era',       default="")
parser.add_argument('-E', '--opts',      dest='extraopts', default=[ ], nargs='+')
parser.add_argument('-p', '--prefetch',  dest='prefetch',  action='store_true')
parser.add_argument('-J', '--jec',       dest='doJEC',     action='store_true')
parser.add_argument('-S', '--jec-sys',   dest='doJECSys',  action='store_true')
parser.add_argument('-U', '--jec-unc',   dest='jesuncs',   default='Total')
args = parser.parse_args()


# SETTING
era       = args.era                # era of data run (e.g. 'UL2016')
year      = getyear(era)            # year of data run (e.g. '2016')
period    = ""                      # period of data run (A-H)
dtype     = args.dtype              # data type ('data', 'mc', 'embed')
outdir    = ensuredir(args.outdir)  # directory to create output
copydir   = args.copydir            # directory to copy output to at end
firstevt  = args.firstevt           # index of first event to run
maxevts   = args.maxevts            # maximum number of events to run
nfiles    = -1 if maxevts>0 else -1 # maximum number of files to run
tag       = args.tag                # postfix tag of job output file
tag       = ('' if not tag or tag.startswith('_') else '_') + tag
postfix   = tag
outfname  = os.path.join(outdir,"*%s.root"%postfix)
url       = "root://cms-xrd-global.cern.ch/"
prefetch  = args.prefetch          # copy input file(s) to ouput directory first
doJEC     = args.doJEC             # apply JECs #and dataType=='data'
doJECSys  = args.doJECSys          # compute JEC variations
jesuncs   = args.jesuncs if doJECSys else '' # type of uncertainties, e.g. 'Total', 'Merged', 'All', ...
presel    = args.preselect         # simple pre-selection string, e.g. for mutau: "HLT_IsoMu27 && Muon_pt>28 && Tau_pt>18" or "Max$(Muon_pt)>20"
commonpresel = args.commonpresel   # common TauPOG pre-selection for lepton and/or jet
branchsel = os.path.join(moddir,"keep_and_drop_skim.txt") # file with branch selection
json      = None                   # JSON file of certified events
modules   = [ ]                    # list of modules to run

# INPUT FILES
infiles   = args.infiles or [ # for testing
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/C9EAE9C3-7392-6B48-8FD2-A2DCA1C6B2C7.root",
  url+"/store/mc/RunIISummer20UL18NanoAODv2/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v15_L1v1-v1/50000/04BBC240-E6D5-824C-9688-835C8D1D9C12.root",
]
if nfiles>0:
  infiles = infiles[:nfiles]

# DATA TYPE
if dtype==None: # guess type
  if any(s in infiles[0] for s in ['SingleMuon',"/Tau/",'SingleElectron','EGamma']):
    dtype = 'data'
  else:
    dtype = 'mc'

## BOOKKEEPING
#from TauFW.PicoProducer.processors.Bookkeeper import Bookkeeper
#modules.append(Bookkeeper(verb=2))

# JET/MET CORRECTIONS & SYSTEMATICS
if 'UL' in era:
  MET = 'MET'
  era = era.replace("_postVFP","") # remove for getjmecalib
else:
  MET = 'METFixEE2017' if ('2017' in era) else 'MET'
if dtype=='data':
  period = getperiod(infiles[0],year,dtype=dtype) # gets data run era (e.g. 'B' from '2016B') from filename
  assert all(str(year) in f for f in infiles), "Not all files names are of the same year '%s': %s"%(year,infiles)
  json  = getjson(era,dtype)
  if doJEC:
    print(">>> Loading createJMECorrector for data, era=%s, pariod=%s..."%(era,period))
    calib = getjmecalib(False,era,runPeriod=period,jetType='AK4PFchs', #,redojec=doJEC
                        noGroom=True,metBranchName=MET,applySmearing=False)()
    modules.append(calib)
elif doJEC or doJECSys:
  print(">>> Loading createJMECorrector for MC, era=%s, pariod=%s..."%(era,period))
  calib   = getjmecalib(True,era,jesUncert=jesuncs,jetType='AK4PFchs', #,redojec=doJEC
                      noGroom=True,metBranchName=MET,applySmearing=True)()
  modules.append(calib)

# PRE-SELECTION
if presel:
  presel = presel.replace('\$','$') # remove escape
elif commonpresel: # common pre-selection for TauPOG studies
  presel = "Max$(Jet_pt)>30 || Max$(Tau_pt)>30 || Max$(Muon_pt)>18 || Max$(Electron_pt)>20"

# BOOKKEEPING
if presel:
  from TauFW.PicoProducer.processors.Bookkeeper import Bookkeeper
  modules.append(Bookkeeper(verb=1)) # order should not matter

# PRINT
print('-'*80)
print(">>> %-12s = %r"%('era',era))
print(">>> %-12s = %r"%('year',year))
print(">>> %-12s = %r"%('period',period))
print(">>> %-12s = %r"%('dtype',dtype))
print(">>> %-12s = %s"%('firstevt',firstevt))
print(">>> %-12s = %s"%('maxevts',maxevts))
print(">>> %-12s = %r"%('tag',tag))
print(">>> %-12s = %r"%('postfix',postfix))
print(">>> %-12s = %r"%('outdir',outdir))
print(">>> %-12s = %r"%('outfname',outfname))
print(">>> %-12s = %r"%('copydir',copydir))
print(">>> %-12s = %s"%('infiles',infiles))
print(">>> %-12s = %r"%('branchsel',branchsel))
print(">>> %-12s = %r"%('json',json))
print(">>> %-12s = %s"%('modules',modules))
print(">>> %-12s = %s"%('prefetch',prefetch))
print(">>> %-12s = %r"%('doJEC',doJEC))
print(">>> %-12s = %r"%('doJECSys',doJECSys))
print(">>> %-12s = %r"%('jesuncs',jesuncs))
print(">>> %-12s = %r"%('cwd',os.getcwd()))
print(">>> %-12s = %r"%('preselection',presel))
print('-'*80)

# RUN
print(">>> Loading post processor...")
p = PostProcessor(outdir,infiles,cut=presel,branchsel=None,outputbranchsel=branchsel,
                  firstEntry=firstevt,maxEntries=maxevts,jsonInput=json,
                  modules=modules,postfix=postfix,noOut=False,prefetch=prefetch)
print(">>> Start post processor...")
p.run()

# GET OUTFILES
basenames = [os.path.basename(f).replace('.root','') for f in infiles] # basenames of output files
outflist = [f for f in glob.glob(outfname) if any(b in f for b in basenames)] # only this job's output
outfiles = ' '.join(outflist)
print(">>> Found outflist = %s"%(outfiles))
if len(outflist)!=len(infiles): # sanity check
  print(">>> WARNING! len(outfiles)=%s != %s = len(infiles)"%(len(outflist),len(infiles)))

# REDUCE FILE SIZE
# Temporary solution to reduce file size
#   https://hypernews.cern.ch/HyperNews/CMS/get/physTools/3734/1.html
#   https://github.com/cms-nanoAOD/nanoAOD-tools/issues/249
#print(">>> Reduce file size...")
#from TauFW.common.tools.utils import execute
#execute("ls -hlt %s"%(outfname),verb=2)
#for outfile in outflist:
#  tmpfile = outfile.replace(".root","_tmp.root")
#  execute("haddnano.py %s %s"%(tmpfile,outfile),verb=2) # reduce file size
#  execute("ls -hlt %s %s"%(tmpfile,outfile),verb=2)
#  execute("mv %s %s"%(tmpfile,outfile),verb=2)
#execute("ls -hlt %s"%(outfname),verb=2)

# COPY
if copydir and outdir!=copydir:
  from TauFW.PicoProducer.storage.utils import getstorage
  from TauFW.common.tools.file import rmfile
  store = getstorage(copydir,verb=2)
  store.cp(outfiles)
  print(">>> Removing %s..."%(outfiles))
  rmfile(outfiles,verb=2)

# DONE
print(">>> skimjob.py done after %.1f seconds"%(time.time()-time0))
