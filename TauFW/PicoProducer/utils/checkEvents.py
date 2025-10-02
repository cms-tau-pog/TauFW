#! /usr/bin/env python
# Author: Izaak Neutelings (Februari 2021)
# Instructions:
#   utils/checkEvents.py output/2016/mutau/DYJetsToLL/*root -T tree
#   utils/checkEvents.py output/2016/mutau/DYJetsToLL/*root -H cutflow -b 1
from TauFW.common.tools.log import color
from TauFW.PicoProducer.storage.utils import LOG, getnevents, isvalid


def main(args):
  files  = args.files
  tname  = args.tree
  hname  = args.hist
  bin    = args.bin
  ntot   = 0
  nfiles = len(files)
  for file in files:
    if hname:
      nevts = isvalid(file,hname,bin) # get nevents from TH1.GetBinContent(bin)
    else:
      nevts = getnevents(file,tname) # get nevents from TTree.GetEntries()
    ntot += nevts
    print ">>> %9d  %s"%(nevts,file)
  print ">>> %9d  total in %d files, average %.1f"%(ntot,nfiles,float(ntot)/nfiles)
  

if __name__ == '__main__':
  from argparse import ArgumentParser
  description = """Trace & print parents of dataset."""
  parser = ArgumentParser(prog="checkEvents",description=description,epilog="Succes!")
  parser.add_argument('files',           nargs='+', default=[ ], action='store',
                      metavar="FNAME",   help="ROOT file to retrieve nevents from" )
  parser.add_argument('-T', '--tree',    type=str, default="Events", action='store',
                                         help="name of tree to retrieve, default=%(default)r" )
  parser.add_argument('-H', '--hist',    type=str, default=None, action='store',
                                         help="name of histogram to retrieve, default=%(default)r" )
  parser.add_argument('-b', '--bin',     type=int, default=1, action='store',
                                         help="bin of histogram to retrieve, default=%(default)d" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main(args)
  
