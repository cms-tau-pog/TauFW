#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test script for Table class
#   test/testTable.py -v2
from TauFW.common.tools.log import Logger
from TauFW.common.tools.Table import Table
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import gRandom, TH1D
LOG = Logger('Test')


def printhist(nevts=10000,verb=0):
  
  # PREPARE HIST
  hist = TH1D('gauss1','gauss1',14,-2,2)
  for i in xrange(nevts):
    hist.Fill(gRandom.Gaus(0,1))
  
  # SIMPLE TABLE
  print ">>> Table from hist"
  table = Table("%9d %10.2f %10.2f",verb=verb)
  table.printheader('ibin','content','error')
  for ibin in range(0,hist.GetXaxis().GetNbins()+1):
    table.printrow(ibin,hist.GetBinContent(ibin),hist.GetBinError(ibin))
  print
  
  # SIMPLE TABLE
  print ">>> Table from hist"
  table = Table("%9s %10s %9s %11s  ","%9d %10.2f  +%7.2f  -%9.2f",verb=verb)
  table.printheader('ibin','content','error up','error down')
  for ibin in range(0,hist.GetXaxis().GetNbins()+1):
    table.printrow(ibin,hist.GetBinContent(ibin),hist.GetBinErrorUp(ibin),hist.GetBinErrorLow(ibin))
  

def main(args):
  verbosity = args.verbosity
  
  # SIMPLE TABLE
  print ">>> Simple table with 3 columns of fixed width"
  table = Table(3,verb=verbosity)
  table.printheader("point","x","y")
  #table.printheader("point","x","y","z") # gives warning
  table.printrow(1,1.0,1.0)
  table.printrow(1,2.0,4.0)
  table.printrow(1,3.0,9.0)
  table.printrow(1,4.0)       # missing column
  table.printrow(1,5.0,25,-1) # surprise extra column
  print
  
  # SIMPLE TABLE
  print ">>> Simple table with custom width"
  table = Table("%6d %8.2f %8.2f ",verb=verbosity)
  table.printheader("point","x","y")
  table.printrow(1,1.0,1.0)
  table.printrow(1,2.0,4.0)
  table.printrow(1,3.0,9.0)
  table.printrow(1,4.0)       # missing column
  table.printrow(1,5.0,25,-1) # surprise extra column
  print
  
  # TABLE with extra symbols
  print ">>> Table with extra symbols"
  table = Table("%8s %8s %8s %6s  ","%6d %8.2f +%5.2f -%5.2f",verb=verbosity)
  table.printheader("point","y","up","down")
  table.printrow(1, 1.0,0.4,0.3)
  table.printrow(1, 4.0,0.7,0.8)
  table.printrow(1, 9.0,2.5,1.5)
  table.printrow(1,16.0,2.8)        # missing columns
  table.printrow(1,25.0)            # missing column
  table.printrow(1,36.0,4.5,3.5,-1) # surprise extra column
  print
  
  # TABLE from LOG
  level = 2
  print ">>> Table from LOG with verbosity level %s:"%(level)
  TAB = LOG.table("%9d %10.2f %10.2f",verb=verbosity,level=level)
  TAB.printheader("point","x","y")
  TAB.printrow(1,1.0,1.0)
  TAB.printrow(1,2.0,4.0)
  TAB.printrow(1,3.0,9.0)
  print
  
  # TABLE of histogram
  printhist(verb=verbosity)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test script for Table class"""
  parser = ArgumentParser(prog="testTable",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  print
  main(args)
  print
  
