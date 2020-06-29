#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Plot class
#   test/plotHists.py && eog plots/hist.png
from TauFW.common.tools.file import ensuredir
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
from ROOT import TH1D, gRandom
from TauFW.Plotter.plot.utils import LOG
LOG.verbosity = 2


def plothist(ratio=False,logy=False):
  
  # SETTING
  outdir   = ensuredir("plots/")
  fname    = outdir+"testhist"
  if ratio:
    fname += "_ratio"
  if logy:
    fname += "_logy"
  nbins    = 50
  xmin     = 0
  xmax     = 100
  nhist    = 3
  nevts    = 100000
  rrange   = 0.5
  xtitle   = "p_{T}^{MET} [GeV]"
  #xtitle   = "Leading jet p_{T} [GeV]"
  text     = "#mu#tau_{h}"
  grid     = True #and False
  lstyle   = 1 # solid
  hists    = [ ]
  
  # HISTS
  gRandom.SetSeed(1777)
  for i in xrange(1,nhist+1):
    hname = "hist%d"%(i)
    hist  = TH1D(hname,hname,nbins,xmin,xmax)
    for j in xrange(nevts):
      hist.Fill(gRandom.Gaus(48+i,10))
    hists.append(hist)
  
  # PLOT
  plot = Plot(xtitle,hists)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,lstyle=lstyle,grid=grid)
  plot.drawlegend()
  plot.drawcornertext(text)
  plot.saveas(fname+".png")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  

def main():
  CMSStyle.setCMSEra(2018)
  #plothist(ratio=False,logy=False)
  for ratio in [True,False]:
    for logy in [True,False]:
      plothist(ratio=ratio,logy=logy)
  

if __name__ == "__main__":
  main()
  
