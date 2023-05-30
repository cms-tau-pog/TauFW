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
#   pico.py run -c stitch -y 2018 -s DYJetsToLL_M-50 DY1J DY2J DY3J DY4J -m 100000 -E 'mutau=True'
#   pico.py submit -c stitch -y 2018 -s DY*JetsToLL -E 'mutau=True'
#   pico.py submit -c stitch -y 2018 -s W*JetsToLNu
#   python/analysis/StitchEffs.py --mutau `for i in '' 1 2 3 4; do echo DY${i}JetsToLL=output/pico_stitch_2018_DY${i}JetsToLL_M-50.root; done`
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
    print(">>> fname   = %r"%(self.fname))
    print(">>> domutau = %r"%(self.domutau))
    print(">>> verb    = %r"%(self.verb))
    
    # HISTOGRAMS
    self.outfile.cd()
    #htbins = [0,1,20,50,70,100,200,400,600,800,1200,2500,4000] # add overflow to last bin
    htbins = [0,70,100,200,400,600,800,1200,2500,4000] # add overflow to last bin
    htargs = (len(htbins)-1,array('d',htbins)) # arguments for variable binning in TH1
    self.h_nup   = TH1D('h_nup',";Number of LHE-level partons;Events",8,0,8)
    self.h_njets = TH1D('h_njets',";Number of reco-level jets (pT > 20 GeV);Events",12,0,12)
    self.h_ht    = TH1D('h_ht', ";LHE-level HT [GeV];Events",*htargs)
    self.h_nup_vs_ht = TH2D('h_nup_vs_ht',";LHE-level HT [GeV];Number of LHE-level partons",len(htbins)-1,array('d',htbins),8,0,8)
    if self.domutau:
      self.h_mutau = TH1D('h_mutau',";Gen. mutau filter;Events",2,0,2)
      self.h_nup_vs_mutau = TH2D('h_nup_vs_mutau',";Gen. mutau filter;Number of LHE-level partons",2,0,2,8,0,8)
    
  def endJob(self):
    """Wrap up after running on all events and files"""
    self.outfile.Write()
    self.outfile.Close()
    
  def analyze(self, event):
    """Process event, return True (pass, go to next module) or False (fail, go to next event)."""
    # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#LHE
    nup = event.LHE_Njets
    ht = min(event.LHE_HT,2501) # add overflow to last bin
    njets20 = 0
    for i in range(event.nJet):
      if event.Jet_pt[i]>20:
        njets20 += 1
    self.h_nup.Fill(nup)
    self.h_njets.Fill(njets20)
    self.h_ht.Fill(ht)
    self.h_nup_vs_ht.Fill(ht,nup)
    if self.domutau:
      mutaufilter = filtermutau(event)
      self.h_mutau.Fill(mutaufilter)
      self.h_nup_vs_mutau.Fill(mutaufilter,nup)
    return False
    

def formattitle(title):
  title = title.replace('HT',"H_{#lower[-0.2]{T}}").replace('pT',"p_{#lower[-0.2]{T}}")
  return title
  
def printtable(hist,norm=False):
  """Print 2D hist as table."""
  header = ">>> "+(10*' ')
  nevts = hist.Integral()
  nxbins = hist.GetXaxis().GetNbins()
  nybins = hist.GetYaxis().GetNbins()
  xint = all(hist.GetXaxis().GetBinWidth(i)==1 for i in range(1,nxbins+1)) # integer bins
  yint = all(hist.GetYaxis().GetBinWidth(i)==1 for i in range(1,nybins+1)) # integer bins
  for xbin in range(1,nxbins+1):
    if xint:
      xstr = "%5.2g"%(hist.GetXaxis().GetBinLowEdge(xbin))
    else:
      xstr = "%.4g-%.4g"%(hist.GetXaxis().GetBinLowEdge(xbin),hist.GetXaxis().GetBinUpEdge(xbin))
    header += " %10s"%(xstr)
  print(header)
  for ybin in range(1,nybins+1):
    if yint:
      ystr = "%5.2g"%(hist.GetYaxis().GetBinLowEdge(ybin))
    else:
      ystr = "%s-%s"%(hist.GetYaxis().GetBinLowEdge(ybin),hist.GetYaxis().GetBinUpEdge(ybin))
    row = ">>> %10s"%(ystr)
    for xbin in range(1,nxbins+1):
      zval = hist.GetBinContent(xbin,ybin)
      if norm and nevts>0:
        zval /= nevts
      row += " %10.5f"%(zval)
    print(row)
  

# QUICK PLOTTING SCRIPT
if __name__ == '__main__':
  from ROOT import gROOT, TFile
  from TauFW.Plotter.plot.Plot import Plot
  from TauFW.Plotter.plot.Plot2D import Plot2D
  from argparse import ArgumentParser
  gROOT.SetBatch(True)      # don't open GUI windows
  gStyle.SetOptTitle(False) # don't make title on top of histogram
  gStyle.SetOptStat(False)  # don't make stat. box
  description = """Make histograms from output file."""
  parser = ArgumentParser(prog="StitchEffs",description=description,epilog="Good luck!")
  parser.add_argument('files', nargs='+', help="final (hadd'ed) ROOT file")
  parser.add_argument('-m',"--mutau", action='store_true', help="plot mutau filter")
  parser.add_argument('-p',"--pdf", action='store_true', help="create PDF version as well")
  parser.add_argument('-t',"--tag", default="", help="extra tag for output file")
  args = parser.parse_args()
  
  # OPEN FILES
  files = [ ]
  hnames = ['h_nup','h_njets','h_ht']
  hnames_2d = ['h_nup_vs_ht']
  if args.mutau:
    hnames.append('h_mutau')
    hnames_2d.append('h_nup_vs_mutau')
  exts = ['png','pdf'] if args.pdf else ['png']
  for fname in args.files:
    if fname.count('=')==1:
      title, fname = fname.split('=')
    else:
      title = fname.split('/')[-1].replace('.root','')
    print(">>> Opening %s (%s)"%(fname,title))
    file = TFile.Open(fname,'READ')
    files.append((title,file))
    
    # PLOT 2D HISTOGRAMS
    for hname in hnames_2d:
      hist = file.Get(hname)
      assert hist, "Did not find %s:%s"%(file.GetName(),hname)
      hist.SetTitle(title)
      nevts = hist.Integral()
      if nevts>0: # normalize
        hist.Scale(100./nevts)
      print(">>> Efficiencies for %s in %s:"%(hname[2:],title))
      printtable(hist,norm=True)
      xtitle = formattitle(hist.GetXaxis().GetTitle())
      ytitle = formattitle(hist.GetYaxis().GetTitle())
      ztitle = "Fraction [%]"
      pname  = "StitchEffs_%s_%s%s"%(hname[2:],args.tag,title.replace(' ',''))
      if 'ht' in hname:
        xmin = 50.
        logx = True
      else:
        xmin = hist.GetXaxis().GetXmin()
        logx = False
      plot = Plot2D(xtitle,ytitle,hist,ztitle=ztitle,clone=True)
      plot.draw('COLZTEXT44',xmin=xmin,logx=logx,tcolor=kRed+1,rmargin=0.185)
      #plot.drawlegend()
      plot.drawtext(title)
      plot.saveas(pname,ext=exts)
      plot.close()
  
  # PLOT HISTOGRAM COMPARISONS
  print(">>> Plot comparisons...")
  for hname in hnames:
    hists = [ ]
    for title, file in files:
      hist = file.Get(hname)
      assert hist, "Did not find %s:%s"%(file.GetName(),hname)
      hist.SetTitle(title)
      nevts = hist.Integral()
      if nevts>0: # normalize
        hist.Scale(100./nevts)
      hists.append(hist)
    xtitle = formattitle(hists[0].GetXaxis().GetTitle())
    ytitle = "Fraction [%]"
    pname  = "StitchEffs_compare_%s%s"%(hname[2:],args.tag)
    rmin, rmax = 0, 3
    if 'ht' in hname:
      xmin = 50.
      logx = True
    else:
      xmin = hists[0].GetXaxis().GetXmin()
      logx = False
    
    # PLOT HISTOGRAMS
    plot = Plot(xtitle,hists,ytitle=ytitle,clone=True)
    plot.draw(ratio=True,xmin=xmin,rmin=rmin,rmax=rmax,logx=logx,lstyle=1)
    plot.drawlegend()
    #plot.drawtext(stitle)
    plot.saveas(pname,ext=exts)
    plot.close()
  
  # CLOSE
  for _, file in files:
    file.Close()
  
  print(">>> Done.")
  
