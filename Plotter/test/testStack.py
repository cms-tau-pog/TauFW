#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test script for Stack class
#   test/testStack.py -v2 && eog plots/testStacks*.png
from array import array
from TauFW.Plotter.plot.utils import LOG, ensuredir
from TauFW.Plotter.plot.Stack import Stack, CMSStyle
from ROOT import TH1D, gRandom, TColor, kBlack, kWhite, kBlue, kOrange, kMagenta
from TauFW.Plotter.plot.Variable import Variable


coldict = { # HTT / TauPOG colors
  'ZTT':  kOrange-4,   'QCD': kMagenta-10,
  'TT':   kBlue-8,     'WJ':  50,
  'ST':   kMagenta-8,  'VV':  TColor.GetColor(222,140,106),
  'data': kBlack,
}


def plotstack(xname,xtitle,datahist,exphists,ratio=False,logy=False):
  """Plot Stack objects for a given data hisogram and list of MC histograms."""
  
  # SETTING
  outdir   = ensuredir("plots")
  fname    = "%s/testStack_%s"%(outdir,xname)
  if ratio:
    fname += "_ratio"
  if logy:
    fname += "_logy"
  rrange   = 0.5
  text     = "#mu#tau_{h} baseline"
  grid     = True and False
  position = 'topright' if logy else 'right'
  
  # PLOT
  LOG.header(fname)
  plot = Stack(xtitle,datahist,exphists)
  plot.draw(ratio=ratio,logy=logy,ratiorange=rrange,grid=grid)
  plot.drawlegend(position=position)
  plot.drawtext(text)
  plot.saveas(fname+".png")
  plot.saveas(fname+".pdf")
  #plot.saveas(fname+".C")
  #plot.saveas(fname+".png",fname+".C")
  #plot.saveas(fname,ext=['png','pdf'])
  plot.close()
  print
  

def createhists(procs,binning,nevts):
  """Prepare histograms for simulated data-MC comparison."""
  
  # BINNING
  if len(binning)==3: # constant binning
    nbins, xmin, xmax = binning
  elif len(binning)==1: # variable binning
    nbins = len(binning[0])-1
    binning = (nbins,array('d',list(binning[0])))
  else:
    raise IOError("Wrong binning: %s"%(binning))
  
  # EXPECTED: PSEUDO MC
  exphists = [ ]
  tothist   = None
  gRandom.SetSeed(1777)
  for hname, htitle, scale, generator, args in procs:
    hist = TH1D(hname,htitle,*binning)
    hist.Sumw2()
    for j in xrange(nevts):
      hist.Fill(generator(*args))
    hist.Scale(scale)
    hist.SetFillColor(coldict.get(hname,kWhite))
    exphists.append(hist)
    if tothist:
      tothist.Add(hist)
    else:
      tothist = hist.Clone('total')
  
  # OBSERVED: PSEUDO DATA
  datahist = TH1D('data','Observed',*binning)
  datahist.SetBinErrorOption(TH1D.kPoisson)
  if LOG.verbosity>=1:
    print ">>> createhists: Creating pseudo data:"
    TAB = LOG.table("%5s [%5s, %5s]      %-14s   %-20s",
                    "%5d [%5s, %5s] %8.1f +- %5.1f %8d +%5.1f -%5.1f")
    TAB.printheader('bin','xlow','xup','exp','data')
  for ibin in xrange(0,nbins+2):
    exp    = tothist.GetBinContent(ibin)
    xlow   = hist.GetXaxis().GetBinLowEdge(ibin)
    xup    = hist.GetXaxis().GetBinUpEdge(ibin)
    experr = tothist.GetBinError(ibin)
    #if ibin==int(0.3*nbins): # add a large deviation to test points falling off ratio plot
    #  exp *= 0.5
    #elif ibin==int(0.8*nbins): # add a large deviation to test points falling off ratio plot
    #  exp *= 1.51
    data   = int(gRandom.Poisson(exp))
    datahist.SetBinContent(ibin,data)
    if LOG.verbosity>=1:
      TAB.printrow(ibin,xlow,xup,exp,experr,data,datahist.GetBinErrorUp(ibin),datahist.GetBinErrorLow(ibin))
  
  return datahist, exphists
  

def main():
  
  CMSStyle.setCMSEra(2018)
  nevts    = 5000
  mvisbins = [0,30,40,50,55,60,65,70,75,80,85,90,95,100,110,120,140,200,300]
  plotset  = [ # make "pseudo"-MC with random generators, and "pseudo" data
    (('m_vis',"m_{vis} [GeV]",40,0,200), [
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus,   ( 72, 9)),
      ('WJ', "W + jets",                1.0, gRandom.Landau, ( 60,28)),
      ('QCD', "QCD multiplet",          0.8, gRandom.Gaus,   ( 90,44)),
      ('TT', "t#bar{t}",                0.8, gRandom.Gaus,   (110,70)),
     ]),
    (('m_vis_var',"m_{vis} [GeV]",mvisbins), [ # variable binning
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus,   ( 72, 9)),
      ('WJ', "W + jets",                1.0, gRandom.Landau, ( 60,28)),
      ('QCD', "QCD multiplet",          0.8, gRandom.Gaus,   ( 90,44)),
      ('TT', "t#bar{t}",                0.8, gRandom.Gaus,   (110,70)),
     ]),
    (('pt_1',"Leading p_{T} [GeV]",50,0,100), [
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.2, gRandom.Landau, (30,2)),
      ('WJ', "W + jets",                0.2, gRandom.Landau, (30,2)),
      ('QCD', "QCD multiplet",          0.3, gRandom.Landau, (37,5)),
      ('TT', "t#bar{t}",                0.2, gRandom.Landau, (48,6)),
     ]),
    (('njets',"Number of jets",8,0,8), [
      ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.2, gRandom.Poisson, (0.2,)),
      ('WJ', "W + jets",                0.2, gRandom.Poisson, (0.4,)),
      ('QCD', "QCD multiplet",          0.3, gRandom.Poisson, (2.0,)),
      ('TT', "t#bar{t}",                0.2, gRandom.Poisson, (2.5,)),
     ]),
    #(Variable('m_vis',"m_{vis} [GeV]",40,0,200), [
    #  ('TT', "t#bar{t}",                1.0, gRandom.Gaus, (120,70)),
    #  ('QCD', "QCD multiplet",          1.2, gRandom.Gaus, ( 80,60)),
    #  ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus, ( 72, 9)),
    # ]),
    #(Variable('m_vis_var',"m_{vis} [GeV]",mvisbins), [ # variable binning
    #   ('TT', "t#bar{t}",                1.0, gRandom.Gaus, (120,70)),
    #   ('QCD', "QCD multiplet",          1.2, gRandom.Gaus, ( 80,60)),
    #   ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.0, gRandom.Gaus, ( 72, 9)),
    # ]),
    #(Variable('njets',"Number of jets",8,0,8), [
    #  ('TT', "t#bar{t}",                0.2, gRandom.Poisson, (2.5,)),
    #  ('QCD', "QCD multiplet",          0.3, gRandom.Poisson, (2.0,)),
    #  ('ZTT', "Z -> #tau_{mu}#tau_{h}", 1.2, gRandom.Poisson, (0.2,)),
    # ]),
  ]
  
  for variable, procs in plotset:
    xname, xtitle = variable[:2]
    binning = variable[2:]
    #plotstack(xtitle,procs,ratio=False,logy=False)
    for ratio in [True,False]:
      for logy in [True,False]:
        datahist, exphists = createhists(procs,binning,nevts)
        plotstack(xname,xtitle,datahist,exphists,ratio=ratio,logy=logy)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Script to test the Plot class for comparing histograms"""
  parser = ArgumentParser(prog="testStack",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  
