#!/usr/bin/env python3
# Author: Izaak Neutelings (November 2023)
# Description: Test RDataFrame to run some samples in parallel
# References:
#   https://root.cern/doc/master/classROOT_1_1RDataFrame.html#parallel-execution
import re
import time
from array import array
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import TNamed, RDataFrame, RDF
#RDataFrame = ROOT.RDF.Experimental.Distributed.Spark.RDataFrame
ROOT.EnableImplicitMT(4)
rexp_esc = re.compile(r"[-+()\[\]\.:]") # escape characters for filename-safe
TNamed.__repr__ = lambda o: "<%s(%r,%r) at %s>"%(o.__class__.__name__,o.GetName(),o.GetTitle(),hex(id(o)))

def took(start_wall,start_cpu,pre=""):
  time_wall = time.time() - start_wall # wall clock time
  time_cpu  = time.perf_counter() - start_cpu # CPU time
  return "%s %d min %.1f sec (CPU: %d min %.1f sec)"%((pre,)+divmod(time_wall,60)+divmod(time_cpu,60))
  

def sampleset_RDF(fnames,tname,vars,sels,weight,rungraphs=True,verb=0):
  print(f">>> sampleset_RDF")
  rdframes = [ ]
  results  = [ ]
  
  # BOOK histograms
  start = time.time(), time.perf_counter() # wall-clock & CPU time
  for fname in fnames:
    rdframe = RDataFrame(tname,fname)
    rdframes.append(rdframe)
    if verb>=1:
      print(f">>> sampleset_RDF:  Created RDF {rdframe} for {fname}...")
    
    # SELECTIONS: add filters
    for sel in sels:
      print(f">>> sampleset_RDF:   Selections {sel!r}...")
      rdf_sel = rdframe.Filter(sel)
      if verb>=1:
        print(f">>> sampleset_RDF:     Created RDF {rdf_sel} with filter {sel!r}...")
      
      # VARIABLES: book histograms
      for vargs in vars:
        xvar    = vargs[0]  # variable name
        xexp    = vargs[0]  # mathematical expression
        bins    = vargs[1:] # histogram binning
        vfname  = rexp_esc.sub('',xvar) # filename
        vtitle  = xvar
        model   = (vfname,vtitle,*bins)
        rdf_var = rdf_sel
        if not rdf_var.HasColumn(xvar): # to compile mathematical expressions
          if verb>=2:
            print(f">>> sampleset_RDF:     Defining {vfname!r} as {xexp!r}...")
          rdf_var = rdf_sel.Define(vfname,xexp) # define column for this variable
          xvar = vfname
        if verb>=2:
          print(f">>> sampleset_RDF:     Booking {xvar!r} with bins {bins} with {rdf_var}...")
        result = rdf_var.Histo1D(model,xvar,weight)
        if verb>=2:
          print(f">>> sampleset_RDF:     Booked {xvar!r}: {result}")
        results.append(result)
  print(f">>> sampleset_RDF: Booking took {took(*start)}")
  
  # RUN
  start = time.time(), time.perf_counter() # wall-clock & CPU time
  if rungraphs:
    print(f">>> sampleset_RDF: Start RunGraphs of {len(results)} results...")
    RDF.RunGraphs(results)
  else:
    print(f">>> sampleset_RDF: Start Draw for {len(results)} results...")
    for result in results:
      print(f">>> sampleset_RDF:   Start {result} ...")
      result.Draw('hist')
  print(f">>> sampleset_RDF: Processing took {took(*start)}")
  

def main(args):
  verbosity = args.verbosity #+2
  indir  = "/scratch/ineuteli/analysis/UL2018"
  tname  = 'tree'
  fnames = args.fnames or [
    f"{indir}/DY/DYJetsToLL_M-50_mutau.root",
    f"{indir}/TT/TTToSemiLeptonic_mutau.root",
    f"{indir}/TT/TTToHadronic_mutau.root",
    f"{indir}/TT/TTTo2L2Nu_mutau.root",
  ]
  weight = "genweight"
  sels = [
    "q_1*q_2<0 && pt_1>20",
    "q_1*q_2>0 && pt_1>20",
    "q_1*q_2>0 && pt_1>40",
  ]
  ptbins = array('d',[0,10,15,20,21,23,25,30,40,60,100,150,200,300,500])
  vars = [
    ('pt_1',50,0,250),
    ('pt_1',len(ptbins)-1,ptbins),
    ('abs(eta_1-eta_2)',50,0,5),
  ]
  sampleset_RDF(fnames,tname,vars,sels,weight,rungraphs=False,verb=verbosity)
  sampleset_RDF(fnames,tname,vars,sels,weight,rungraphs=True,verb=verbosity)
  sampleset_RDF(fnames,tname,vars,sels,weight,rungraphs=False,verb=verbosity)
  sampleset_RDF(fnames,tname,vars,sels,weight,rungraphs=True,verb=verbosity)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test RDataFrame."""
  parser = ArgumentParser(description=description,epilog="Good luck!")
  parser.add_argument('-i', '--fnames',    nargs='+', help="input files" )
  parser.add_argument('-t', '--tag',       default="", help="extra tag for output" )
  parser.add_argument('-n', '--ncores',    default=4, type=int, help="number of cores, default=%(default)s" )
  parser.add_argument('-v', '--verbose',   dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                           help="set verbosity" )
  args = parser.parse_args()
  main(args)
  print("\n>>> Done.")
