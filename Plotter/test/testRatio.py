#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test script for Ratio class
#   test/testRatio.py -v2 && eog plots/testRatio*.png
from TauFW.Plotter.plot.utils import LOG, ensuredir
from TauFW.Plotter.plot.Plot import Plot, Variable, CMSStyle
from TauFW.Plotter.plot.Stack import Stack
from testPlot import createhists
from testStack import createhists as createhists_obsexp
from ROOT import gRandom


def plothist(hists,ratio=False,num=False):
  """Plot comparison of histograms."""
  
  # SETTING
  outdir   = ensuredir("plots/")
  fname    = outdir+"testRatio_%dhist_ratio%r"%(len(hists),ratio)
  if num!=None:
    fname += "_num%r"%(num)
  xtitle   = "p_{T}^{MET} [GeV]"
  rrange   = 0.5
  grid     = True #and False
  norm     = True #and False  # normalize all histograms
  staterr  = True and False  # add uncertainty band to first histogram
  
  # PLOT
  LOG.header(fname)
  plot = Plot(xtitle,hists,norm=norm,clone=True)
  plot.draw(ratio=ratio,num=num,logy=False,ratiorange=rrange,grid=True,staterr=staterr)
  plot.drawlegend('topright',header="Gaussians")
  plot.drawtext("Ratio = %r"%(ratio),"Num = %r"%(num))
  plot.saveas(fname+".png")
  plot.close()
  print('')
  

def plotstack(xname,xtitle,datahist,exphists,ratio=False,fraction=False,logy=False):
  """Plot Stack objects for a given data hisogram and list of MC histograms."""
  
  # SETTING
  outdir   = ensuredir("plots")
  fname    = "%s/testRatio_stack_%s"%(outdir,xname)
  if ratio:
    fname += "_ratio"
  if fraction:
    fname += "_frac"
  rrange   = 0.5
  text     = "#mu#tau_{h} baseline"
  grid     = True and False
  position = 'topright' if logy else 'right'
  
  # PLOT
  LOG.header(fname)
  plot = Stack(xtitle,datahist,exphists,clone=True)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,grid=grid,fraction=fraction)
  plot.drawlegend(position=position)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  plot.saveas(fname+".pdf")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  print('')
  

def main():
  
  # SET CMSSTYLE
  CMSStyle.setCMSEra(2018)
  
  # HISTOGRAM COMPARISON
  for nhists in [2,3]:
    hists = createhists(nhist=nhists)
    for ratio in [True,0,1,2,3,-1]:
      nums = [None,0,1,2,3,-1] if isinstance(ratio,bool) and ratio else [None]
      for num in nums:
        plothist(hists,ratio=ratio,num=num)
      
  # DATA / MC COMPARISON
  nevts    = 5000
  mvisbins = [0,30,40,50,55,60,65,70,75,80,85,90,95,100,110,120,140,200,300]
  plotset  = [ # make "pseudo"-MC with random generators, and "pseudo" data
    (('mvis',"m_{vis} [GeV]",40,0,200), [
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus,   ( 72, 9)),
      ('WJ', "W + jets",                1.0, gRandom.Landau, ( 60,28)),
      ('QCD', "QCD multiplet",          0.8, gRandom.Gaus,   ( 90,44)),
      ('TT', "t#bar{t}",                0.8, gRandom.Gaus,   (110,70)),
     ]),
    (('mvis_var',"m_{vis} [GeV]",mvisbins), [ # variable binning
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus,   ( 72, 9)),
      ('WJ', "W + jets",                1.0, gRandom.Landau, ( 60,28)),
      ('QCD', "QCD multiplet",          0.8, gRandom.Gaus,   ( 90,44)),
      ('TT', "t#bar{t}",                0.8, gRandom.Gaus,   (110,70)),
     ]),
  ]
  
  for variable, procs in plotset:
    xname, xtitle = variable[:2]
    binning = variable[2:]
    datahist, exphists = createhists_obsexp(procs,binning,nevts) # make "pseudo"-MC with random generators, and "pseudo" data
    for ratio in [True,0,1,2,3,-1]:
      fractions = [True,False] if ratio else [False]
      for fraction in fractions:
        plotstack(xname,xtitle,datahist,exphists,ratio=ratio,fraction=fraction)
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = '''Script to test the Plot class for comparing histograms.'''
  parser = ArgumentParser(prog="testPlot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity level" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
