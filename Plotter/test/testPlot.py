#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Plot class
#   test/testPlot.py -v2 && eog plots/testPlot*.png
from TauFW.Plotter.plot.utils import LOG, ensuredir
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
from ROOT import TH1D, gRandom


def plothist(xtitle,hists,ratio=False,logy=False,norm=False):
  
  # SETTING
  outdir   = ensuredir("plots/")
  fname    = outdir+"testPlot"
  if ratio:
    fname += "_ratio"
  if logy:
    fname += "_logy"
  if norm:
    fname += "_norm" # normalize each histogram
  rrange   = 0.5
  width    = 0.2             # legend width
  position = 'topright'      # legend position
  header   = "Gaussians"     # legend header
  text     = "#mu#tau_{h}"   # corner text
  grid     = True #and False
  staterr  = True and False  # add uncertainty band to first histogram
  lstyle   = 1               # solid lines
  
  # PLOT
  LOG.header(fname)
  plot = Plot(xtitle,hists,norm=norm)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid,staterr=staterr)
  plot.drawlegend(position,header=header,width=width)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  plot.saveas(fname+".pdf")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  print
  

def createhists(nhist=3):
  nbins    = 50
  xmin     = 0
  xmax     = 100
  nevts    = 10000
  rrange   = 0.5
  hists    = [ ]
  gRandom.SetSeed(1777)
  for i in xrange(1,nhist+1):
    mu     = 48+i
    sigma  = 10
    hname  = "hist%d"%(i)
    htitle = "#mu = %s, #sigma = %s"%(mu,sigma)
    hist   = TH1D(hname,hname,nbins,xmin,xmax)
    for j in xrange(nevts):
      hist.Fill(gRandom.Gaus(mu,sigma))
    hists.append(hist)
  return hists
  

def main():
  
  CMSStyle.setCMSEra(2018)
  xtitle = "p_{T}^{MET} [GeV]"
  #xtitle = "Leading jet p_{T} [GeV]"
  
  #plothist(variable,hists,ratio=False,logy=False)
  for ratio in [True,False]:
    for logy in [True,False]:
      for norm in [True,False]:
        hists = createhists()
        plothist(xtitle,hists,ratio=ratio,logy=logy,norm=norm)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = '''Script to test the Plot class for comparing histograms.'''
  parser = ArgumentParser(prog="testPlot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
