#! /usr/bin/env python
# Author: Izaak Neutelings (September 2020)
# Description: Test EventBased splitting
#   test/testEventBased.py
import os, platform
from time import sleep
from TauFW.common.tools.file import ensureTFile
from TauFW.common.tools.math import partition_by_max, ceil
from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
from TauFW.PicoProducer.storage.Sample import Sample, LOG
from TauFW.PicoProducer.storage.utils import getsamples
from ROOT import TFile


def chunkify_by_evts(fnames,nmax,evenly=True):
  result  = [ ]
  nlarge  = { }
  nsmall  = { }
  for fname in fnames:
    file  = ensureTFile(fname,'READ')
    nevts = file.Get('Events').GetEntries()
    file.Close()
    print "%10d %s"%(nevts,fname)
    if nevts<nmax:
      nsmall.setdefault(nevts,[ ]).append(fname)
    else:
      nlarge.setdefault(nevts,[ ]).append(fname)
  #nlarge = {
  #  1081403L: ['nano_1.root'],
  #  2235175L: ['nano_2.root'],
  #   144447L: ['nano_3.root'],
  #  #1515407L: ['nano_4.root'],
  #    200000: ['nano_5.root'],
  #    150000: ['nano_6.root'],
  #    100000: ['nano_7.root'],
  #}
  #nsmall = {
  #     50000: ['nano_8.root', 'nano_9.root', 'nano_10.root'],
  #     20000: ['nano_11.root','nano_12.root','nano_13.root'],
  #}
  print 'nlarge =',nlarge
  print 'nsmall =',nsmall
  for nevts in nlarge:
    for fname in nlarge[nevts]:
      nmax_ = nmax
      if evenly:
        nchunks = ceil(float(nevts)/nmax)
        nmax_   = int(ceil(nevts/nchunks))
        print nevts,nmax,nmax_,nchunks
      ifirst = 0
      while ifirst<nevts:
        result.append(["%s:%d:%d"%(fname,ifirst,nmax_)])
        ifirst += nmax_
  mylist = [ ]
  for nevts in nsmall:
    mylist.extend([nevts]*len(nsmall[nevts]))
  for part in partition_by_max(mylist,nmax):
    result.append([ ])
    for nevts in part:
      fname = nsmall[nevts][0]
      nsmall[nevts].remove(fname)
      result[-1].append(fname+":%d"%nevts)
  return result


def testEventBased(verb=0):
  storage  = None #"/eos/user/i/ineuteli/samples/nano/$ERA/$PATH"
  url      = None #"root://cms-xrd-global.cern.ch/"
  filelist = None #"samples/files/2016/$SAMPLE.txt"
  samples  = [
    M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
    #"/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext2-v1/NANOAODSIM",
    store=storage,url=url,
    ),
    #M('TT','TT',
    #  "/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7-v2/NANOAODSIM",
    #  store=storage,url=url,
    #),
    #D('Data','SingleMuon_Run2016C', "/SingleMuon/Run2016C-Nano25Oct2019-v1/NANOAOD",
    #  store=storage,url=url,
    #),
  ]
  for sample in samples:
    print sample
    files = sample.getfiles()[:8]
    chunks = chunkify_by_evts(files,nmax=100000)
    for chunk in chunks:
      print chunk
  

def main(args):
  testEventBased(args)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test event-based splitting of files."""
  parser = ArgumentParser(prog="testBatch",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose',    dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                            help="set verbosity" )
  parser.add_argument('-m','--maxevts',     dest='maxevts', type=int, default=None,
                                            help='maximum number of events (per file) to process')
  #parser.add_argument('-f','--force',       dest='force', action='store_true',
  #                                          help='force overwrite')
  #parser.add_argument('-d','--dry',         dest='dryrun', action='store_true',
  #                                          help='dry run: prepare job without submitting for debugging purposes')
  #parser.add_argument('-N','--ntasks',      dest='ntasks', type=int, default=2,
  #                    metavar='N',          help='number of tasks per job to submit, default=%(default)d' )
  #parser.add_argument('-n','--nchecks',     dest='nchecks', type=int, default=5,
  #                    metavar='N',          help='number of job status checks, default=%(default)d' )
  ##parser.add_argument('--getjobs',          dest='checkqueue', type=int, nargs='?', const=1, default=-1,
  ##                        metavar='N',      help="check job status: 0 (no check), 1 (check once), -1 (check every job)" ) # speed up if batch is slow
  #parser.add_argument('-B','--batch-opts',  dest='batchopts', default=None,
  #                                          help='extra options for the batch system')
  #parser.add_argument('-M','--time',        dest='time', default=None,
  #                                          help='maximum run time of job')
  #parser.add_argument('-q','--queue',       dest='queue', default=None,
  #                                          help='queue of batch system (job flavor on HTCondor)')
  ##parser.add_argument('-P','--prompt',      dest='prompt', action='store_true',
  ##                                          help='ask user permission before submitting a sample')
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
