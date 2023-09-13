#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Plot class
#   test/testPlot.py -v2 && eog plots/testPlot*.png
from TauFW.Plotter.plot.utils import LOG, ensuredir, deletehist
from TauFW.Plotter.plot.Plot import Plot, CMSStyle
from TauFW.common.tools.root import rootrepr
from ROOT import TH1D, gRandom


def testPlot_init(xtitle,hists,norm=False,clone=False):
  """Test Plot.__init__ with different arguments."""
  from TauFW.Plotter.plot.Plot import Var
  
  # SETTING
  outdir = ensuredir("plots/")
  fname  = outdir+"testPlot_init"
  if clone:
    fname += "_norm" # normalize each histogram
  if norm:
    fname += "_clone" # normalize each histogram
  
  # CREATE DIFFERENT ARGUMENTS
  xvar  = Var('x',xtitle,100,0,100)
  hists1 = clonehists(hists,t='a')
  hists2 = clonehists(hists,t='b')
  h1, h2, h3 = hists2[:3] # assume at least three
  argset = [
    (hists1),
    (h1,h2,h3),
  ]
  for i, x in enumerate([xtitle,xvar],1):
    hists1 = clonehists(hists,t='c%s'%i)
    hists2 = clonehists(hists,t='d%s'%i)
    h1, h2, h3 = hists2[:3] # assume at least three
    argset += [
      (x,hists1),
      (x,h1,h2,h3),
    ]
  
  # PLOT
  for i, args in enumerate(argset,1):
    fname_ = "%s_%s"%(fname,i)
    LOG.header("%s"%(fname_))
    print(">>> args=%s"%(rootrepr(args)))
    print(">>> norm=%r, clone=%r"%(norm,clone))
    plot = Plot(*args,norm=norm,clone=clone)
    plot.draw(ratio=False)
    #plot.drawtext(text)
    plot.saveas(fname_+".png")
    plot.close()
    print('')
  

def plothist(xtitle,hists,ratio=False,logy=False,norm=False,cwidth=None):
  """Plot comparison of histograms."""
  
  # SETTING
  outdir   = ensuredir("plots/")
  fname    = outdir+"testPlot"
  if ratio:
    fname += "_ratio"
  if logy:
    fname += "_logy"
  if norm:
    fname += "_norm" # normalize each histogram
  if cwidth:
    fname += "_W%d"%(cwidth)
  rrange   = 0.5
  lwidth   = 0.2             # legend width
  position = 'topright'      # legend position
  header   = "Gaussians"     # legend header
  text     = "#mu#tau_{h}"   # corner text
  grid     = True #and False
  staterr  = True and False  # add uncertainty band to first histogram
  lstyle   = 1               # solid lines
  
  # PLOT
  LOG.header(fname)
  print(">>> norm=%r, ratio=%r, logy=%r, cwidth=%r"%(norm,ratio,logy,cwidth))
  plot = Plot(xtitle,hists,norm=norm)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,width=cwidth,lstyle=lstyle,grid=grid,staterr=staterr)
  plot.drawlegend(position,header=header,width=lwidth)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  plot.saveas(fname+".pdf")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  print('')
  

def createhists(nhist=3):
  """Create some histograms of gaussian distributions."""
  nbins    = 50
  xmin     = 0
  xmax     = 100
  nevts    = 10000
  rrange   = 0.5
  hists    = [ ]
  gRandom.SetSeed(1777)
  for i in range(1,nhist+1):
    mu     = 48+i
    sigma  = 10
    hname  = "hist%d"%(i)
    htitle = "#mu = %s, #sigma = %s"%(mu,sigma)
    hist   = TH1D(hname,hname,nbins,xmin,xmax)
    for j in range(nevts):
      hist.Fill(gRandom.Gaus(mu,sigma))
    hists.append(hist)
  return hists


def clonehists(hists,t=''):
  """Clone histogram with unique name."""
  return [h.Clone(h.GetName()+"_clone%s%s"%(i,t)) for i, h in enumerate(hists,1)]
  

def main():
  
  CMSStyle.setCMSEra(2018)
  xtitle = "p_{T}^{MET} [GeV]"
  #xtitle = "Leading jet p_{T} [GeV]"
  ratios  = [True,False]
  logys   = [True,False]
  norms   = [True,False]
  cwidths = [800,500,1400]
  
  # TEST PLOTTING ROUTINE with different combination of common style options
  #plothist(variable,hists,ratio=False,logy=False)
  for ratio in ratios:
    for logy in logys:
      for norm in norms:
        for cwidth in cwidths:
        #for cwidth in [None,1000]:
          hists = createhists()
          plothist(xtitle,hists,ratio=ratio,logy=logy,norm=norm,cwidth=cwidth)
  
  # TEST INITIATION with different arguments
  for clone in [True,False]:
    for norm in [True,False]:
      hists = createhists(3)
      testPlot_init(xtitle,hists,norm=norm,clone=clone)
      deletehist(hists)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = '''Script to test the Plot class for comparing histograms.'''
  parser = ArgumentParser(prog="testPlot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity level" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
