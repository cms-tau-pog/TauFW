#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Plot.drawlegend
#   test/testLegend.py -v2 && eog plots/testLegend*.png
from TauFW.Plotter.plot.utils import LOG, ensuredir, deletehist
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
from testPlot import createhists
from ROOT import TH1D, gRandom


def plothist(xtitle,hists,ratio=False,logy=False,norm=False,tag="",**kwargs):
  
  # SETTING
  outdir   = ensuredir("plots/")
  fname    = outdir+"testLegend"
  rrange   = 0.5
  header   = "Gaussians"     # legend header
  text     = "#mu#tau_{h}"   # corner text
  grid     = True and False
  staterr  = True and False  # add uncertainty band to first histogram
  lstyle   = 1               # solid lines
  panel    = 1               # 1 = main (top) panel, 2 = ratio (bottom) panel
  #hists    = [h.Clone("%s_clone%d"%(h.GetName(),i)) for i, h in enumerate(hists)]
  if kwargs.get('pos',False):
    fname += "_"+kwargs['pos'].replace(';','')
    header = kwargs['pos']
  if ratio:
    fname += "_ratio"
  fname += tag
  
  # PLOT
  LOG.header(fname)
  plot = Plot(xtitle,hists,norm=norm,clone=True)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid,staterr=staterr)
  plot.drawlegend(border=True,header=header,panel=panel,**kwargs)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  #plot.saveas(fname+".pdf")
  plot.close(keep=False)
  print
  

def testposition():
  """Test positioning of drawlegend."""
  xtitle = "p_{T}^{MET} [GeV]"
  hists = createhists(2)
  for ratio in [False]: # True
    plothist(xtitle,hists,ratio=ratio,logy=True,norm=False)
    for hor in ['','L','LL','R','RR','C','CL','CR']:
      for ver in ['','T','TT','B','BB','M']:
        pos = (hor+'-'+ver).strip('-')
        plothist(xtitle,hists,ratio=ratio,logy=True,norm=False,pos=pos)
  deletehist(hists)
  

def testwidth():
  """Test automatic width of drawlegend."""
  xtitle  = "p_{T}^{MET} [GeV]"
  entries = [
    "short",
    "Z -> tautau",
    "Z #rightarrow #tau_{h}tau_{h}",
    "p_{T} > 20 GeV, |#eta| < 2.5",
    "p_{T} > 20 GeV, 2.5 < |#eta| < 4.7",
    "this is medium long",
    "this is a very long legend entry",
    "this is a very long Z -> tautau",
    "line one\nline two",
  ]
  hists   = createhists(2)
  for i, entry in enumerate(entries):
    tag = "_width%d"%(i)
    hists[0].SetTitle(entry)
    plothist(xtitle,hists,ratio=False,logy=True,norm=False,tag=tag) #,pos='R'
  deletehist(hists)
  

def main():
  CMSStyle.setCMSEra(2018)
  #testposition()
  testwidth()
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test script for Plot.drawlegend"""
  parser = ArgumentParser(prog="testLegend",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
