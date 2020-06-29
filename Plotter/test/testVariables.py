#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test Variable initiation
#   test/testVariables.py
from TauFW.common.tools.log import color
from TauFW.Plotter.plot.utils import LOG, gDirectory
from TauFW.Plotter.plot.Variable import Variable
LOG.verbosity = 1



def main():
  
  mvisbins  = [0,30,40,50,60,70,75,80,90,100,120,200]
  variables = [
    Variable('m_vis',     "m_{vis} [GeV]", 40, 0,200),
    Variable('njets',     "Number of jets", 8, 0,  8),
    Variable('m_vis',     40, 0,200),
    Variable('njets',      8, 0,  8),
    Variable('njets',      8, 0,  8, veto='njets'),
    Variable('st',        20, 0,800, title="S_{T}",only="njets",blind="st>600"),
    Variable('m_vis',     40, 0,200, cbins={'njets':mvisbins},blind=(70,90)),
    Variable('m_vis',      mvisbins, cbins={"njets[^&]*2":(40,0,200)},),
    Variable('pt_1+pt_2', 20, 0,800, title="S_{T}^{tautau}",ctitle={"njets":"S_{T}"}),
  ]
  selections = [
    "pt_1>50 && pt_2>50",
    "pt_1>50 && pt_2>50 && njets>=1",
    "pt_1>50 && pt_2>50 && njets>=2 && nbtags>=1",
    "pt_1>50 && pt_2>50 && njets==0",
    "pt_1>50 && pt_2>50 && dzeta>-40",
  ]
  
  for var in variables:
    LOG.header(var.name)
    print ">>> string=%s, repr=%r"%(var,var)
    print ">>> name='%s', title='%s'"%(color(var.name),color(var.title))
    print ">>> (nbins,xmin,xmax)=(%s,%s,%s), bins=%s"%(var.nbins,var.xmin,var.xmax,var.bins)
    print ">>> hasintbins=%s, hasvariablebins=%s"%(var.hasintbins(),var.hasvariablebins())
    print ">>> cut=%r, blindcuts=%r, blind(50,60)=%r"%(var.cut,var.blindcuts,var.blind(50,60))
    hist = var.gethist()
    print ">>> hist=%s, (nbins,xmin,xmax)=(%s,%s,%s), variable=%s"%(
               hist,hist.GetXaxis().GetNbins(),hist.GetXaxis().GetXmin(),hist.GetXaxis().GetXmax(),hist.GetXaxis().IsVariableBinSize())
    gDirectory.Delete(hist.GetName())
    for sel in selections:
      var.changecontext(sel)
      print ">>> context: '%s'"%color(sel,'grey')
      print ">>>   plotfor=%s, name='%s', title='%s'"%(var.plotfor(sel),color(var.name),color(var.title))
      print ">>>   (nbins,xmin,xmax)=(%s,%s,%s), bins=%s"%(var.nbins,var.xmin,var.xmax,var.bins)
    print
  

if __name__ == "__main__":
  main()
  
