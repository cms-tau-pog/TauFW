#!/usr/bin/env python3
# Author: Izaak Neutelings (November 2023)
# Description: Test RDataFrame to run some samples in parallel
# References:
#   https://root.cern/doc/master/classROOT_1_1RDataFrame.html#parallel-execution
#   https://root-forum.cern.ch/t/using-a-python-dictionary-in-rdataframe-define-using-a-column-as-the-key/47787
import os, re
import time
from array import array
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import gROOT, gStyle, TNamed, RDataFrame, RDF, TFile, TCanvas, TLegend,\
                 kRed, kGreen, kBlue, kMagenta
print(">>> Done importing...")

#RDataFrame = ROOT.RDF.Experimental.Distributed.Spark.RDataFrame
gROOT.SetBatch(True) # don't open GUI windows
gStyle.SetOptTitle(False) # don't make title on top of histogram
ROOT.EnableImplicitMT(4) # number of cores
rexp_esc  = re.compile(r"[-+()\[\]\.:]") # escape characters for filename-safe
rexp_stit = re.compile(r"([^/]+).root") # get filename without extension
TNamed.__repr__ = lambda o: "<%s(%r,%r) at %s>"%(o.__class__.__name__,o.GetName(),o.GetTitle(),hex(id(o)))
#RDF.RInterface.__repr__ = lambda o: "xxx<%s(%r,%r) at %s>"%(o.__class__.__name__,o.GetName(),o.GetTitle(),hex(id(o)))
lcolors = [kBlue+1, kRed+1, kGreen+1, kMagenta+1]

# PROGRESS BAR
ROOT.gInterpreter.Declare("""
  // Based on https://root-forum.cern.ch/t/onpartialresult-and-progress-bar-with-pyroot/39739/4
  // Note: Escape the '\' when defined in python string
  namespace ROOT::RDF {
    const UInt_t barWidth = 40; int everyN = 0;
    ULong64_t processed = 0, totalEvents = 0;
    std::string progressBar;
    std::mutex barMutex;
    auto registerEvents = [](ULong64_t nIncrement) { totalEvents += nIncrement; };
    RResultPtr<ULong64_t> AddProgressBar(RNode df, int everyN=10000, int totalN=100000) {
      registerEvents(totalN);
      auto c = df.Count();
      c.OnPartialResultSlot(everyN,[everyN](unsigned int slot, ULong64_t &cnt){
        std::lock_guard<std::mutex> l(barMutex);
        processed += everyN; // everyN captured by value for this lambda
        progressBar = ">>> [";
        for(UInt_t i = 0; i < static_cast<UInt_t>(static_cast<Float_t>(processed)/totalEvents*barWidth); ++i){
          progressBar.push_back('=');
        }
        std::cout << "\\r" << std::left << std::setw(barWidth+4) << progressBar << "] " << processed << "/" << totalEvents << " " << std::flush;
      });
      return c;
    };
    void stopProgressBar(ULong64_t ntot=totalEvents) {
      std::cout << "\\r" << std::left << std::setw(barWidth+4) << progressBar << "] Processed " << ntot << " events" << std::flush << std::endl;
      processed = 0; totalEvents = 0; // reset
    };
  }
""")
print(">>> Done declaring.")


def dmmap(dm='dm_2'):
  return f"{dm}==0 ? 0 : ({dm}==1 || {dm}==2) ? 1 : {dm}==10 ? 2 : {dm}==11 ? 3 : 4"
  

def took(start_wall,start_cpu,pre=""):
  time_wall = time.time() - start_wall # wall clock time
  time_cpu  = time.perf_counter() - start_cpu # CPU time
  return "%s %d min %.1f sec (CPU: %d min %.1f sec)"%((pre,)+divmod(time_wall,60)+divmod(time_cpu,60))
  

def plot(fname,hists,verb=0):
  print(f">>> plot: {fname!r}: {hists!r}")
  canvas = TCanvas('canvas','canvas',100,100,1000,800) # XYWH
  canvas.SetMargin(0.10,0.04,0.11,0.02) # LRBT
  canvas.SetLogy()
  canvas.SetTicks(1,0) # draw ticks on opposite side
  #legend = TLegend()
  for hist, color in zip(hists,lcolors):
    hist.SetLineWidth(2)
    hist.SetLineColor(color)
    hist.Draw('HIST E1 SAME')
  #legend.Draw()
  canvas.BuildLegend()
  canvas.SaveAs(fname)
  canvas.Close()
  

def sampleset_RDF(fnames,tname,vars,sels,rungraphs=True,verb=0):
  print(f">>> sampleset_RDF")
  results  = [ ]
  counts   = [ ]
  res_dict = { } # { selection : { variable: [ hist1, ... ] } }
  
  # BOOK histograms
  start = time.time(), time.perf_counter() # wall-clock & CPU time
  for stitle, fname, weight in fnames:
    rdframe = RDataFrame(tname,fname)
    #nevts = int(rdframe.Count().GetValue()) # this might add a couple of seconds
    file = TFile.Open(fname,'READ'); nevts = file.Get(tname).GetEntries(); file.Close() # fast !
    RDF.AddProgressBar(RDF.AsRNode(rdframe),max(100,int(nevts/2000)),int(nevts))
    wname = weight
    if verb>=1:
      print(f">>> sampleset_RDF: Created RDF {rdframe!r} for {fname}...")
    if not rdframe.HasColumn(wname): # to compile mathematical expressions in xvar
      wname = "_rdf_sample_weight"
      if verb>=1:
        print(f">>> sampleset_RDF:   Defining {wname!r} as {weight!r}...")
      rdframe = rdframe.Define(wname,weight) # define column for this variable
    
    # SELECTIONS: add filters
    for sname, sel in sels:
      print(f">>> sampleset_RDF:   Selections {sel!r}...")
      #cname = "_rdf_sample_cut" # define new column for better performance ?
      #rdf_sel = rdframe.Define(cname,sel).Filter(cname)
      rdf_sel = rdframe.Filter(sel)
      if verb>=1:
        print(f">>> sampleset_RDF:     Created RDF {rdf_sel!r} with filter {sel!r}...")
      
      # VARIABLES: book histograms
      for vname, vexp, *bins in vars:
        model   = (vname,stitle,*bins) # RDF.TH1DModel
        rdf_var = rdf_sel
        if not rdf_var.HasColumn(vexp): # to compile mathematical expressions in xvar
          if verb>=2:
            print(f">>> sampleset_RDF:     Defining {vname!r} as {vexp!r}...")
          rdf_var = rdf_var.Define(vname,vexp) # define column for this variable
          vexp = vname
        if verb>=2:
          print(f">>> sampleset_RDF:     Booking {vname!r} with model {model!r} and RDF {rdf_var!r}...")
        result = rdf_var.Histo1D(model,vexp,wname)
        #counts.append(ROOT.AddProgressBar(ROOT.RDF.AsRNode(rdf_var)))
        if verb>=2:
          print(f">>> sampleset_RDF:     Booked {vname!r}: {result!r}")
        results.append(result)
        res_dict.setdefault(sname,{ }).setdefault(vname,[ ]).append(result) #.GetValue()
  print(f">>> sampleset_RDF: Booking took {took(*start)}")
  
  # RUN events loops to fill histograms
  start = time.time(), time.perf_counter() # wall-clock & CPU time
  if rungraphs:
    print(f">>> sampleset_RDF: Start RunGraphs of {len(results)} results...")
    RDF.RunGraphs(results)
    RDF.stopProgressBar()
  else:
    print(f">>> sampleset_RDF: Start Draw for {len(results)} results...")
    for result in results:
      #print(f">>> sampleset_RDF:   Start {result} ...")
      #result.Draw('HIST')
      result.GetValue() # trigger event loop
    RDF.stopProgressBar()
  print(f">>> sampleset_RDF: Processing took {took(*start)}")
  
  # PLOT histograms
  for sname in res_dict:
    for vname in res_dict[sname]:
      fname = f"{vname}_{sname}.png"
      hists = [r.GetValue() for r in res_dict[sname][vname]]
      plot(fname,hists,verb=verb)
  

def main(args):
  ROOT.EnableImplicitMT(args.ncores) # number of cores
  verbosity = args.verbosity #+2
  indir  = "/scratch/ineuteli/analysis/UL2018"
  tname  = 'tree'
  fnames = args.fnames or [
    ('DYJets',  f"{indir}/DY/DYJetsToLL_M-50_mutau.root",  "2.65e-5*genweight"), # 5343/201506219
    ('TTTo2L2N',f"{indir}/TT/TTTo2L2Nu_mutau.root",        "5.61e-9*genweight"), #  88.29/15748570179.6
    ('TTToHadr',f"{indir}/TT/TTToHadronic_mutau.root",     "2.57e-9*genweight"), # 377.96/146924304906.7
    ('TTToSemi',f"{indir}/TT/TTToSemiLeptonic_mutau.root", "2.05e-9*genweight"), # 365.35/177965649707.7
  ]
  sels = [
    ("ss_ptgt20","q_1*q_2<0 && pt_1>20 && pt_2>20"),
    ("os_ptgt20","q_1*q_2>0 && pt_1>20 && pt_2>20"),
    ("os_ptgt40","q_1*q_2>0 && pt_1>40 && pt_2>40"),
  ]
  ptbins = array('d',[0,10,15,20,21,23,25,30,40,60,100,150,200,300,500])
  vars = [
    ('pt_1',      'pt_1',            50,0,250),
    ('pt_1_rebin','pt_1',            len(ptbins)-1,ptbins),
    ('deta',      'abs(eta_1-eta_2)',50,0, 5),
    ('dm_2',      'dm_2',            14,0,14),
    ('dm_2_map',  dmmap(),           6,0, 6),
  ]
  sampleset_RDF(fnames,tname,vars,sels,rungraphs=False,verb=verbosity)
  sampleset_RDF(fnames,tname,vars,sels,rungraphs=True,verb=verbosity)
  

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
