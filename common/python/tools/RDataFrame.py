# -*- coding: utf-8 -*-
# Author: Izaak Neutelings (August 2020)
import os
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import gROOT, gInterpreter, RDataFrame, RDF

#### NOTE: RDataFrame parallelizes over TTree clusters, check tree->Print("clusters")
###if ROOT.GetThreadPoolSize()==0:
###  ROOT.EnableImplicitMT(4) # default number of threads

# REPRESENTATION: shorten for debugging
RDataFrame.__repr__ = lambda o: "<%s at %s>"%(o.__class__.__name__,hex(id(o)))
RDF.RInterface['ROOT::Detail::RDF::RJittedFilter,void'].__repr__ = lambda o: "<RInterface<RJittedFilter,void> at %s>"%(hex(id(o)))
for temp in ['TH1D','TH2D','ULong64_t','double']: # templates
  RDF.RResultPtr[temp].__repr__ = lambda o: "<%s at %s>"%(o.__class__.__name__,hex(id(o)))

# PROGRESS BAR
gInterpreter.Declare("""
  // Based on https://root-forum.cern.ch/t/onpartialresult-and-progress-bar-with-pyroot/39739/4
  // Note: Escape the '\' character in python string
  namespace ROOT::RDF {
    const UInt_t barWidth = 40; int everyN = 0;
    ULong64_t processed = 0, totalEvents = 0;
    int maxpostlen = 0; // to remove long post
    std::string progressBar;
    std::mutex barMutex; // to avoid concurrent printing (only one thread at a time can lock a mutex)
    auto registerEvents = [](ULong64_t nIncrement) { totalEvents += nIncrement; };
    RResultPtr<ULong64_t> _AddProgressBar(RNode df, int everyN=10000, int totalN=100000,std::string post="") {
      registerEvents(totalN);
      auto c = df.Count();
      if(maxpostlen<post.length())
        maxpostlen = post.length();
      c.OnPartialResultSlot(everyN,[everyN,post](unsigned int slot, ULong64_t &cnt){
        std::lock_guard<std::mutex> lg(barMutex); // lock the mutex at construction, releases it at destruction
        processed += everyN; // everyN captured by value for this lambda
        if(totalEvents==0) return;
        progressBar = ">>> [";
        for(UInt_t i=0; i<static_cast<UInt_t>(static_cast<Float_t>(processed)/totalEvents*barWidth); ++i){
          progressBar.push_back('=');
        }
        std::cout << "\\r" << std::left << std::setw(barWidth+4) << progressBar << "] "
                  << processed << "/" << totalEvents << std::setw(maxpostlen) << post << " " << std::flush;
      });
      return c;
    };
    void _StopProgressBar(ULong64_t ntot=totalEvents, std::string post="") {
      if(progressBar!="" and processed>0)
        std::cout << "\\r" << std::left << std::setw(barWidth+4) << progressBar << "] Processed "
                  << ntot << " events"  << std::setw(maxpostlen) << post << std::flush << std::endl;
      progressBar = ""; processed = 0; totalEvents = 0; // reset
    };
    void _StopProgressBar(std::string post) { _StopProgressBar(totalEvents,post); };
  }
""")


def AddProgressBar(rdframe,totalN,post="",verb=0):
  """Help-function to add progress bar to given RDataFrame, converting input objects to required format."""
  everyN = min(max(400,totalN/200.),25000)
  if verb>=1:
    print(">>> AddProgressBar: Add %r with everyN=%s, totalN=%s, post=%r"%(rdframe,everyN,totalN,post))
  return RDF._AddProgressBar(RDF.AsRNode(rdframe),int(everyN),int(totalN),ROOT.std.move(ROOT.std.string(post)))
RDF.AddProgressBar = AddProgressBar # save as part of RDF module


def StopProgressBar(post=""):
  """Help-function to stop progress bar after running RDataFrame."""
  return RDF._StopProgressBar(ROOT.std.string(post))
RDF.StopProgressBar = StopProgressBar # save as part of RDF module


def SetNumberOfThreads(nthreads=None,verb=0):
  """Set number of threads.
  If nthreads==None: Change nothing.
  If nthreads==0, 1: Serial (disable multithreading).
  If nthreads==True: allow 8 threads (default)."""
  # NOTE:
  #   1) RDataFrame parallelizes over TTree clusters, check tree->Print("clusters")
  #   2) After creating of RDataFrame, the number of threads cannot be changed anymore
  if nthreads==None: # do not do anything
    return ROOT.GetThreadPoolSize()
  else:
    if isinstance(nthreads,bool):
      nthreads = min(8,os.cpu_count()) if nthreads else 1 # if nthreads==True: set to default 8 cores
    if verb>=1:
      print(">>> SetNumberOfThreads: Setting number of threads from %s to %s..."%(ROOT.GetThreadPoolSize(),nthreads))
    if ROOT.IsImplicitMTEnabled(): #ROOT.GetThreadPoolSize()<=0:
      if verb>=2:
        print(">>> SetNumberOfThreads: Calling ROOT.DisableImplicitMT...")
      ROOT.DisableImplicitMT() # turn off to overwrite previous setting
    if nthreads>=2: # only enable implicit multithreading if one or more threads are requested
      if verb>=2:
        print(">>> SetNumberOfThreads: Calling ROOT.EnableImplicitMT(%s)..."%(nthreads))
      ROOT.EnableImplicitMT(nthreads)
  if ROOT.GetThreadPoolSize()!=nthreads:
    print(">>> SetNumberOfThreads: Warning! Number of threads is set to ROOT.GetThreadPoolSize()=%s instead of the requested nthreads=%s..."%(
      ROOT.GetThreadPoolSize(),nthreads))
  return nthreads
RDF.SetNumberOfThreads = SetNumberOfThreads


def printRDFReport(report,reorder=False):
  """Print cutflow from RCutFlowReport."""
  print(">>> \033[4m%10s %10s %10s %10s    %s\033[0m"%("Pass","All","Eff. [%]","Cum. [%]","Selection"+' '*50))
  evt_dict = { }
  if reorder: # (naively) reorder cuts (by default cuts are ordered according to the order of RDataFrame.Filter calls)
    for cut in report:
      if cut.GetPass() not in evt_dict:
        evt_dict[cut.GetPass()] = [ ] # add "parent" cut
      if cut.GetAll() in evt_dict: # assume first cut with cut1.GetPass()==cut2.GetAll() is "parent" cut
        evt_dict[cut.GetAll()].append(cut) # add "child" cut
  def printcut(cut,indent=""): # help-function to print recursively
    if reorder and cut in skipcuts: return # cut already printed
    cumeff = 100.*cut.GetPass()/ntot # cumulative efficiency
    print(">>> %10d %10d %10.2f %10.2f    %s"%(cut.GetPass(),cut.GetAll(),cut.GetEff(),cumeff,indent+cut.GetName()))
    if reorder: # recursively print "child" cuts
      skipcuts.append(cut)
      for subcut in evt_dict.get(cut.GetPass(),[ ]): # loop over "child" cuts
        printcut(subcut,indent+"  ") # print "child" cuts
  ntot = None # all events processed by RDataFrame
  skipcuts = [ ] # cuts which already have been displayed
  for cut in report: # iterate over TCutInfo in RCutFlowReport
    if ntot==None: # assume first cut has total of all events processed by RDataFrame
      ntot = cut.GetAll()
    printcut(cut,indent="")
  

def AddRDFColumn(self,cexpr,basename="_rdf_col",expr_dict=None,exact=False,verb=0):
  """Define new column in RDF if it does not exist, while ensuring unique column name and avoid duplicates.
  To avoid duplicate definition of the same expression, one can keep track via a dictionary (expr_dict)."""
  # cexpr: mathematical expression to be defined in column
  # cname: column name for cexpr
  # basename: string to define cname if needed (numbers may be added to create unique name)
  # expr_dict = { cexpr: cname }: dictionary to look up cname for given cexpr (if already defined)
  if cexpr and not isinstance(cexpr,str):
    cexpr = cexpr.name # assume cexpr is a Variable object
  rdframe, cname = self, cexpr
  if not cexpr: # cname not defined (empty string?)
    cname = ""
    if verb>=4:
      print(">>> RDataFrame.AddRDFColumn: Ignoring %r in %r..."%(cname,self))
  elif expr_dict and cexpr in expr_dict: # already defined in expr_dict !
    cname = expr_dict[cexpr] # reuse unique column name for this variable
  else: # if mathematical expression: compile & define column in RDF with unique column name
    if exact: # assert that column with name cname is not defined yet !
      cname = basename # use this exact column name for cexpr
      if self.HasColumn(cname):
        print(">>> AddRDFColumn: Could not uniquely define expression %r as column %r, because column %r already exists in %r! Ignoring..."%(
              cexpr,cname,cname,rdframe))
      else: # define first time
        rdframe = self.Define(cname,cexpr) # compile expression as new column called cname
        if verb>=2:
          print(">>> RDataFrame.AddRDFColumn: Defining %r (exact) as %r in %r..."%(cname,cexpr,self))
    elif not self.HasColumn(cexpr): # column does not exist yet, define cexpr with column name cname
      i = 1
      cname = basename+"1"
      while self.HasColumn(cname): # ensure column name is unique
        i += 1
        cname = basename+str(i)
      rdframe = self.Define(cname,cexpr) # compile expression as new column called cname
      if verb>=2:
        print(">>> RDataFrame.AddRDFColumn: Defining %r (i=%d) as %r in %r..."%(cname,i,cexpr,self))
    elif verb>=4: # column already defined !
      print(">>> RDataFrame.AddRDFColumn: Column %r already defined in %r! Ignoring..."%(cname,self))
    if expr_dict!=None and cname!=cexpr and cexpr not in expr_dict: # not yet in expr_dict
      expr_dict[cexpr] = cname # save column name for reuse by other variables
  return rdframe, cname
RDataFrame.EnsureColumn = AddRDFColumn # add as new class method
