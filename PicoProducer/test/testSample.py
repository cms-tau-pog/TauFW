#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test Sample class
#   test/testSample.py -v2
from TauFW.common.tools.log import color
from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
from TauFW.PicoProducer.storage.Sample import Sample, LOG
from TauFW.PicoProducer.storage.utils import getsamples, repkey


def testSample(args):
  
  era       = "2016"
  storage   = None #"/eos/user/i/ineuteli/samples/nano/$ERA/$PATH"
  url       = None #"root://cms-xrd-global.cern.ch/"
  filelist  = None #"samples/files/2016/$SAMPLE.txt"
  verbosity = args.verbosity
  samples   = [
    M('DY','DYJetsToLL_M-50',
      "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
      "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext2-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts='zpt=True',
    ),
    M('TT','TT',
      "/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts='toppt=True',
    ),
    M('WJ','W4JetsToLNu',
      "/W4JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/lathomas-NANOAODv2Step_UL16nonAPV-ae987f664fa23fba95446c7ef5426a19/USER",
      store=storage,url=url,files=filelist, #instance='prod/phys03',
    ),
    D('Data','SingleMuon_Run2016C', "/SingleMuon/Run2016C-Nano25Oct2019-v1/NANOAOD",
      store=storage,url=url,files=filelist,
    ),
  ]
  filters = args.filters
  terms = [
    'DY',
    'DY*Jets',
    'DY?Jets',
    'DY[1J]',
    'DY*pythia8',
  ] + filters
  
  # PRINT
  listname = "test/files/$ERA/$SAMPLE.txt"
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
    print ">>> %-14s = %r"%("files",sample.files)
    print ">>> %-14s = %r"%("nevents",sample.nevents)
    
    # MATCH
    print ">>> Testing matching:"
    for term in terms:
      match = sample.match(term,verb=verbosity)
      match = color('YES','green',b=True) if match else color('NO','red',b=True)
      print ">>> %r matches to %r: %s"%(sample.name,term,match)
    if filters and not all(sample.match(f,verb=verbosity) for f in filters):
      continue
    
    # WRITE
    fname = repkey(listname,ERA=era)
    print ">>>\n>>> Write..."
    sample.writefiles(fname,nevts=True) # write Sample.files to txt file
    print ">>> %-14s = %r"%("listname",fname)
    #print ">>> %-14s = %r"%("files",sample.files)
    print ">>> %-14s = %r"%("nfiles",len(sample.files))
    print ">>> %-14s = %r"%("nevents",sample.nevents)
    
    # LOAD
    print ">>>\n>>> Reset..."
    newsample = Sample(sample.group,sample.name,*sample.paths,
                       store=storage,url=url,files=fname,opts=sample.extraopts)
    print ">>> %-14s = %r"%("listname",fname)
    print ">>> %-14s = %r"%("files",newsample.files)
    print ">>> %-14s = %r"%("nfiles",len(newsample.files))
    print ">>> %-14s = %r"%("nevents",newsample.nevents)
    print ">>> Call Sample.getfiles..." # load Sample.files from txt file
    files = newsample.getfiles()
    print ">>> %-14s = %r"%("files",newsample.files)
    print ">>> %-14s = %r"%("nfiles",len(newsample.files))
    print ">>> %-14s = %r"%("nevents",newsample.nevents)
    print ">>> %-14s = %r"%("filenevts",newsample.filenevts)
    

def testModule(era):
  dtypes  = None
  channel = None
  filters = None
  vetoes  = None
  samples = getsamples(era,channel=channel,dtype=dtypes,filter=filters,veto=vetoes)
  

def main(args):
  testSample(args)
  #testModule('2016')
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Script to test the Plot class for comparing histograms."""
  parser = ArgumentParser(prog="testSample",description=description,epilog="Good luck!")
  parser.add_argument('-s', '--sample',  dest='filters', type=str, nargs='+', default=[ ],
                      metavar='PATTERN', help="filter these samples; glob patterns like '*' and '?' wildcards are allowed")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
