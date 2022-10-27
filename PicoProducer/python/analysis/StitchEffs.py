#! /usr/bin/env python
# Author: Izaak Neutelings (May 2022)
# Description:
#   Module to Measure efficiency of (LHE-level) HT- vs. Njet binned
#   in DY*Jets*(HT) and W*Jets*(HT) MadGraph samples for stitching
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/MCStitching
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#LHE
# Instructions:
#   pico.py channel stitch StitchEffs
#   pico.py run -c stitch -y 2018 -s DYJetsToLL_M-50 `for i in 1 2 3 4; do echo DY${i}JetsToLL_M-50; done` -m 10000 -E 'mutau=True'
#   pico.py run -c stitch -y UL2018 -s WJetsToLNu WJetsToLNu_HT-70to100 -m 10000
#   python/analysis/StitchEffs.py output/pico_genmutau_UL2018_DYJetsToLL_M-50.root
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import re
from array import array
from ROOT import TFile, TH1D, TH2D, gStyle, kRed
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from TauFW.PicoProducer.analysis.utils import filtermutau


class StitchEffs(Module):
  """Simple module to study efficiency of (LHE-level) HT- / Njets bins."""
  
  def __init__(self,fname,**kwargs):
    self.fname   = fname
    self.outfile = TFile(fname,'RECREATE') # make custom file with only few histograms
    self.verb    = kwargs.get('verb', 0    )
    self.domutau = kwargs.get('mutau',False)
    print ">>> fname   = %r"%(self.fname)
    print ">>> domutau = %r"%(self.domutau)
    print ">>> verb    = %r"%(self.verb)
    
    # HISTOGRAMS
    self.outfile.cd()
    htbins = [70,100,200,400,600,800,1200,2500,3000] # add overflow to last bin
    htargs = (len(htbins)-1,array('d',htbins)) # arguments for variable binning in TH1
    self.h_nup = TH1D('h_nup',";Number of LHE-level partons;Events",8,0,8)
    self.h_ht  = TH1D('h_ht', ";LHE-level HT [GeV];Events",*htargs)
    self.h_nup_vs_ht = TH2D('h_nup_vs_ht',";LHE-level HT [GeV];Number of LHE-level partons",len(htbins)-1,array('d',htbins),8,0,8)
    if self.domutau:
      self.h_mutau = TH1D('h_mutau',";Gen. mutau filter;Events",2,0,2)
      self.h_mutau_vs_nup = TH2D('h_mutau_vs_nup',";Number of LHE-level partons;Gen. mutau filter",8,0,8,2,0,2)
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#LHE
    self.h_nup.Fill(event.LHE_Njets)
    self.h_nup_vs_ht.Fill(event.LHE_HT,event.LHE_Njets)
    if self.domutau:
      mutaufilter = filtermutau(event)
      self.h_mutau.Fill(mutaufilter)
      self.h_mutau_vs_nup.Fill(event.LHE_Njets,mutaufilter)
    return False
    

#### QUICK PLOTTING SCRIPT
###if __name__ == '__main__':
###  from ROOT import gROOT, TFile
###  from TauFW.Plotter.plot.Plot import Plot
###  from argparse import ArgumentParser
###  gROOT.SetBatch(True)      # don't open GUI windows
###  gStyle.SetOptTitle(False) # don't make title on top of histogram
###  gStyle.SetOptStat(False)  # don't make stat. box
###  description = """Make histograms from output file."""
###  parser = ArgumentParser(prog="GenMatcher",description=description,epilog="Good luck!")
###  parser.add_argument('files', nargs='+', help="final (hadd'ed) ROOT file")
###  parser.add_argument('-t',"--tag", default="", help="extra tag for output file")
###  args = parser.parse_args()
###  
###  # OPEN FILES
###  files = [ ]
###  for fname in args.files:
###    if fname.count('=')==1:
###      title, fname = fname.split('=')
###    else:
###      title = fname.replace('.root','')
###    print ">>> Opening %s (%s)"%(fname,title)
###    file = TFile.Open(fname,'READ')
###    tree = file.Get('tree')
###    tree.title = title
###    tree.file = file
###    trees.append(tree)
###    
###    # CHECK MUTAU FILTER EFFICIENCY
###    hist = file.Get('h_mutaufilter')
###    
###    xtitle = trees[0].GetBranch(xvar).GetTitle() #xvar
###    pname  = "%s_%s%s"%(xvar,sname,args.tag)
###    hists  = [ ]
###    
###    # PLOT HISTOGRAMS
###    print ">>> Plotting..."
###    plot = Plot(xtitle,hists,clone=True)
###    plot.draw(ratio=True,lstyle=1)
###    plot.drawlegend()
###    plot.drawtext(stitle)
###    plot.saveas(pname,ext=['png']) #,'pdf'
###    plot.close()
###  print ">>> Done."
  
