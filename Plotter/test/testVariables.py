#! /usr/bin/env python
# Author: Izaak Neutelings (June 2020)
# Description: Test Variable initiation and contextual behavior
#   test/testVariables.py
#   test/testVariables.py -v -V mtau -S dm_2
from TauFW.common.tools.log import color
from TauFW.Plotter.plot.string import filtervars
from TauFW.Plotter.plot.utils import LOG, gDirectory
from TauFW.Plotter.plot.Variable import Variable
LOG.verbosity = 1



def main(args):
  
  varfilters = args.varfilters
  selfilters = args.selfilters
  mvisbins   = [0,30,40,50,60,70,75,80,90,100,120,200]
  
  # Test several initializations of Variable object.
  # Note that key-word arguments starting with 'c' are used for context-dependent attributes
  mtau_window = { # restrict the tau mass window for tau energy scale measurements
   'dm_2==1(?!0)(?!1)': '0.35<m_2 && m_2<1.20', # [ 0.3, 1.3*sqrt(pt/100) ]
   'dm_2==10':          '0.83<m_2 && m_2<1.43', # [ 0.8, 1.5 ] -> +-3%: [ 0.824, 1.455 ], +-2%: [ 0.816, 1.470 ]
   'dm_2==11':          '0.93<m_2 && m_2<1.53', # [ 0.9, 1.6 ] -> +-3%: [ 0.927, 1.552 ], +-2%: [ 0.918, 1.568 ]
  }
  variables = [
    Variable('mvis',     "m_{vis} [GeV]", 40, 0,200),
    Variable('njets',     "Number of jets", 8, 0,  8),
    Variable('m_vis',     40,  0,200),
    Variable('njets',      8,  0,  8),
    Variable('njets',      8,  0,  8, veto='njets'),
    Variable('st',        20,  0,800, title="S_{T}",only="njets",blind="st>600"),
    Variable('mtau',      13,0.3,1.6, cut="0.3<m_2 && m_2<1.6",ccut=mtau_window,veto="dm_2==0"),
    Variable('mvis',      40,  0,200, cbins={'njets':mvisbins},blind=(70,90)),
    Variable('mvis',      mvisbins, cbins={"njets[^&]*2":(40,0,200)},),
    Variable('pt_1+pt_2', 20,  0,800, title="S_{T}^{tautau}",ctitle={"njets":"S_{T}"}),
  ]
  selections = [
    "pt_1>50 && pt_2>50",
    "pt_1>50 && pt_2>50 && njets>=1",
    "pt_1>50 && pt_2>50 && njets>=2 && nbtags>=1",
    "pt_1>50 && pt_2>50 && njets==0",
    "pt_1>50 && pt_2>50 && dzeta>-40",
    "pt_1>50 && pt_2>50 && dm_2==0",
    "pt_1>50 && pt_2>50 && dm_2==1",
    "pt_1>50 && pt_2>50 && dm_2==10",
    "pt_1>50 && pt_2>50 && dm_2==11",
  ]
  if varfilters:  # filter variable list with -V flag
    variables = filtervars(variables,varfilters)
  if selfilters:  # filter variable list with -V flag
    selections = filtervars(selections,selfilters)
  
  for var in variables:
    LOG.header(var.name)
    print ">>> string=%s, repr=%r"%(var,var)
    print ">>> name='%s', filename='%s', title='%s'"%(color(var.name),color(var.filename),color(var.title))
    print ">>> (nbins,xmin,xmax)=(%s,%s,%s), bins=%s"%(var.nbins,var.xmin,var.xmax,var.bins)
    print ">>> hasintbins=%s, hasvariablebins=%s"%(var.hasintbins(),var.hasvariablebins())
    print ">>> cut=%r, blindcuts=%r, blind(50,60)=%r"%(var.cut,var.blindcuts,var.blind(50,60))
    hist = var.gethist()
    print ">>> hist=%s, (nbins,xmin,xmax)=(%s,%s,%s), variable=%s"%(
               hist,hist.GetXaxis().GetNbins(),hist.GetXaxis().GetXmin(),hist.GetXaxis().GetXmax(),hist.GetXaxis().IsVariableBinSize())
    gDirectory.Delete(hist.GetName())
    for sel in selections: # context-dependent attributes
      var.changecontext(sel)
      print ">>> context: '%s'"%color(sel,'grey')
      print ">>>   plotfor=%s, name='%s', title='%s'"%(var.plotfor(sel),color(var.name),color(var.title))
      print ">>>   (nbins,xmin,xmax)=(%s,%s,%s), bins=%s, cut=%r"%(var.nbins,var.xmin,var.xmax,var.bins,var.cut)
    print
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Test Variable initiation"""
  parser = ArgumentParser(prog="testVariables",description=description,epilog="Good luck!")
  parser.add_argument('-V', '--var',     dest='varfilters', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilters', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, default=1, action='store',
                                         help="set verbosity, default=%(default)d" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  
