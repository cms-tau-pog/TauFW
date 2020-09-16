#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test Sample class
#   test/testSample.py -v2
from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
from TauFW.PicoProducer.storage.Sample import Sample, LOG
from TauFW.PicoProducer.storage.utils import getsamples


def testSample():
  
  storage  = None #"/eos/user/i/ineuteli/samples/nano/$ERA/$PATH"
  url      = None #"root://cms-xrd-global.cern.ch/"
  filelist = None #"samples/files/2016/$SAMPLE.txt"
  samples  = [
    M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext2-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
    ),
    M('TT','TT',
      "/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7-v2/NANOAODSIM",
      store=storage,url=url,file=filelist,opts='toppt=True',
    ),
    D('Data','SingleMuon_Run2016C', "/SingleMuon/Run2016C-Nano25Oct2019-v1/NANOAOD",
      store=storage,url=url,file=filelist,
    ),
  ]
  terms = [
    'DY',
    'DY*Jets',
    'DY?Jets',
    'DY[1J]',
  ]
  
  # PRINT
  for sample in samples:
    LOG.header(sample.name)
    print ">>> %-14s = %r"%("group",sample.group)
    print ">>> %-14s = %r"%("name",sample.name)
    print ">>> %-14s = %r"%("paths",sample.paths)
    print ">>> %-14s = %r"%("url",sample.url)
    print ">>> %-14s = %r"%("era",sample.era)
    print ">>> %-14s = %r"%("channels",sample.channels)
    print ">>> %-14s = %r"%("storage",sample.storage)
    print ">>> %-14s = %r"%("extraopts",sample.extraopts)
    print ">>> %-14s = %r"%("nfilesperjob",sample.nfilesperjob)
    for term in terms:
      match = sample.match(term,verb=4)
  

def testModule(era):
  dtypes  = None
  channel = None
  filters = None
  vetoes  = None
  samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes)
  

def main():
  testSample()
  #testModule('2016')
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Script to test the Plot class for comparing histograms."""
  parser = ArgumentParser(prog="testSample",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print "\n>>> Done."
  
