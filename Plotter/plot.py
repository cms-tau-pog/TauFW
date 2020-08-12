#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Simple plotting script for pico analysis tuples
#   ./plot.py
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG

def plot(sampleset,channel,tag="",outdir="plots"):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot")
  
  baseline = 'q_1*q_2<0 && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter'
  selections = [
    Sel('baseline',baseline),
  ]
  variables = [
    Var('m_vis', 40,  0, 200),
    Var('mt_1',  "mt(mu,MET)", 40,  0, 200),
    Var('pt_1',  "Muon pt",    40,  0, 120, ),
    Var('pt_2',  "tau_h pt",   40,  0, 120, ),
    Var('eta_1', "Muon eta",   30, -3, 3, ymargin=1.6, ncols=2),
    Var('eta_2', "tau_h eta",  30, -3, 3, ymargin=1.6, ncols=2),
    Var('njets', 8,  0,  8),
    Var('rawDeepTau2017v2p1VSjet_2', 'rawDeepTau2017v2p1VSjet', 22, 0.78, 1, pos='left'),
  ]
  text = "#mu#tau_{h} baseline" if channel=='mutau' else "e#tau_{h} baseline"
  
  # PLOT
  outdir   = ensuredir(outdir)
  parallel = True #and False
  fname    = "%s/plot_$VAR$TAG"%(outdir)
  for selection in selections:
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',parallel=parallel)
    for stack, variable in stacks.iteritems():
      #position = "" #variable.position or 'topright'
      stack.draw()
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=['png','pdf'],tag=tag)
      stack.close()
  

def main(args):
  channels = args.channels
  eras     = args.eras
  outdir   = "plots"
  tag      = ""
  fname    = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style
      sampleset = getsampleset(channel,era,fname=fname)
      plot(sampleset,channel,tag="",outdir=outdir)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau'], default=['mutau'], action='store',
                                         help="set channel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
