#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Test loading of methods
#   test/testMethods.py -v2
from TauFW.Plotter.sample.utils import LOG, SampleSet
from TauFW.common.tools.file import ensuremodule

def main():
  methods = [ 'QCD_OSSS' ]
  for method in methods:
    methodmod = ensuremodule(method,'Plotter.methods')
    print ">>> hasattr(SampleSet,%r) = %s, module=%s"%(method,hasattr(SampleSet,method),methodmod)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Test loading of methods"""
  parser = ArgumentParser(prog="testMethods",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print "\n>>> Done."
  
