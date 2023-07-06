#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test joining or stitching of Sample objects
#   test/testStitching.py -v2
from TauFW.Plotter.sample.utils import LOG, STYLE, setera, CMSStyle, ensuredir,\
                                       join, Sample, MergedSample, SampleSet
from pseudoSamples import makesamples

def printsamples(samples,title=None):
  if title:
    print(">>> %s:"%(title))
  for sample in samples:
    print(">>>   %r: %r"%(sample.name,sample))
  

def joinsamples(samples,tag="",outdir="plots"):
  """Test join."""
  LOG.header("joinsamples")
  name    = "DY_merged"
  title   = "DY merged"
  samples = samples[:]
  printsamples(samples,title="Before")
  join(samples,"DY*Jets",name=name)
  printsamples(samples,title="After")
  

def joinSampleSet(samples,tag="",outdir="plots"):
  """Test SampleSet.join."""
  LOG.header("joinSampleSet")
  name    = "DY_merged"
  title   = "DY merged"
  samples = SampleSet(samples)
  samples.printtable("Before:")
  samples.join("DY*Jets",name=name)
  print(">>> ")
  samples.printtable("After:")
  

def stitchSampleSet(samples,tag="",outdir="plots",xsec=1.00):
  """Test SampleSet.join."""
  LOG.header("stitchSampleSet")
  name    = "DY_stiched"
  title   = "DY stiched"
  samples = SampleSet(samples)
  samples.printtable("Before:")
  samples.stitch("DY*Jets",incl='DYJ',name="DY",title="Drell-Yan",xsec=1.00)
  print(">>> ")
  samples.printtable("After:")
  

def main():
  LOG.header("Prepare samples")
  sampleset = [
    ('WJ',   "W + jets",            0.40),
    ('QCD',  "QCD multijet",        0.30),
    ('DYJetsToLL',  "DY incl.",     1.00),
    ('DY1JetsToLL', "DY + 1 jet",   0.50),
    ('DY2JetsToLL', "DY + 2 jet",   0.30),
    ('DY3JetsToLL', "DY + 3 jet",   0.20),
    ('DY4JetsToLL', "DY + 4 jet",   0.10),
    ('TT',   "t#bar{t}",            0.15),
    #('Data', "Observed",             -1 ),
  ]
  lumi     = setera(2018,0.001) # [fb-1] to cancel xsec [pb]
  nevts    = 50000
  snames   = [n[0] for n in sampleset]
  scales   = {n[0]: n[2] for n in sampleset} # relative contribtions to pseudo data
  outdir   = ensuredir('plots')
  indir    = outdir
  filedict = makesamples(nevts,sample=snames,scales=scales,outdir=outdir)
  samples  = [ ]
  for name, title, xsec in sampleset:
    file, tree = filedict[name]
    fname = file.GetName()
    file.Close()
    sample = Sample(name,title,fname,xsec)
    samples.append(sample)
  joinsamples(samples,outdir=outdir)
  joinSampleSet(samples,outdir=outdir)
  stitchSampleSet(samples,outdir=outdir,xsec=1.00)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test joining or stitching of Sample objects"""
  parser = ArgumentParser(prog="testStitching",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print("\n>>> Done.")
  
