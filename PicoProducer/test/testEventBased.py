#! /usr/bin/env python
# Author: Izaak Neutelings (September 2020)
# Description: Test EventBased splitting
#   test/testEventBased.py
#   test/testEventBased.py filesplit.root evtsplit.root
#   test/testEventBased.py '*_filesplit.root' '*_evtsplit.root' -T Events
import os, platform
from time import sleep
from TauFW.common.tools.file import ensureTFile
from TauFW.common.tools.math import partition_by_max, ceil
from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
from TauFW.PicoProducer.storage.Sample import Sample, LOG
from TauFW.PicoProducer.storage.utils import getsamples
#from TauFW.PicoProducer.batch.utils import chunkify_by_evts
from ROOT import TFile, TChain, TH1F


def chunkify_by_evts(fnames,nmax,evenly=True):
  """Test implementation of event-based splitting of large files to limit number of events
  to process during jobs with a given maximum. Small files are still grouped as long as their
  total events is less than the maximum.
  For full implementation, see TauFW.PicoProducer.batch.utils"""
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


def testEventBased(args,verb=0):
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
  

def gettree(fname,tree='tree'):
  """Get file and tree. If glob pattern, expand and use TChain."""
  if '*' in fname:
    fnames = glob.glob(fname)
    file = None
    tree = TChain(tree)
    for fname in fnames:
      tree.Add(fname)
  else:
    file = ensureTFile(fname)
    tree = file.Get(tree)
  return file, tree
  

def compare_output(args,verb=0):
  """Quick comparison between job output."""
  print ">>> Compare job output..."
  nbins  = 100000
  fname1 = "/scratch/ineuteli/analysis/2016/DY/DYJetsToLL_M-2000to3000_tautau.root"      # file-based split
  fname2 = "/scratch/ineuteli/analysis/2016/DY/DYJetsToLL_M-2000to3000_tautau_test.root" # event-based split
  if len(args.infiles)>=2:
    fname1, fname2 = args.infiles[:2]
  tname = args.tree
  ename = args.evt
  print ">>>  ",fname1
  print ">>>  ",fname2
  file1, tree1 = gettree(fname1,tname)
  file2, tree2 = gettree(fname2,tname)
  hist1  = TH1F('h1','h1',nbins,0,1000000)
  hist2  = TH1F('h2','h2',nbins,0,1000000)
  tree1.Draw("%s >> h1"%(ename),"","gOff")
  tree2.Draw("%s >> h2"%(ename),"","gOff")
  print ">>>   tree1: %9d, hist1: %9d"%(tree1.GetEntries(),hist1.GetEntries())
  print ">>>   tree2: %9d, hist2: %9d"%(tree2.GetEntries(),hist2.GetEntries())
  hist1.Add(hist2,-1)
  nfound = 0
  for i in range(0,nbins+2):
    if nfound==20:
      print ">>>    BREAK! Already found 20 different bins"
      break
    if hist1.GetBinContent(i)!=0.0:
      print ">>>    difference in bin %4d!"
      nfound += 1
  if file1:
    file1.Close()
  if file2:
    file2.Close()
  

def main(args):
  if args.infiles:
    compare_output(args)
  else:
    testEventBased(args)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test event-based splitting of files."""
  parser = ArgumentParser(prog="testBatch",description=description,epilog="Good luck!")
  parser.add_argument('infiles',         type=str, nargs='*', default=[], action='store',
                                         help="files to compare" )
  parser.add_argument('-T', '--tree',    action='store', default='tree',
                                         help="tree name, default=%(default)s" )
  parser.add_argument('-e', '--evt',     action='store', default='evt',
                                         help="event branch name, default=%(default)s" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  parser.add_argument('-m','--maxevts',  dest='maxevts', type=int, default=None,
                                         help='maximum number of events (per file) to process')
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
