#! /usr/bin/env python
# Author: Jacopo Malvaso (August 2022)
# Description: Simple plotting script for pico analysis tuples
#   test/plotPico.py -v2
import re
import sys
#print(sys.path)
import os 
from TauFW.Plotter.sample.utils import getsampleset, setera
from TauFW.common.tools.file import ensuredir
from TauFW.common.tools.log import LOG
from TauFW.Plotter.plot.Variable import Var
import TauFW.Plotter.sample.SampleStyle as STYLE

def makesamples(channel,era,fname):
  LOG.header("makesamples")
  weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2" 
  expsamples = [ # table of MC samples to be converted to Sample objects
    ('WJ',              "WJetsToLNu", "W + jets", 52760*1.166 ),
    ('WJ',    "WJetsToLNuHT100to200", "W + jets", 1395.0*1.166),
    ('WJ',   " WJetsToLNuHT200to400", "W + jets", 407.9*1.166 ),
    ('WJ',   " WJetsToLNuHT400to600", "W + jets", 57.48*1.166 ),
    ('WJ',   " WJetsToLNuHT600to800", "W + jets", 12.87*1.166 ),
    ('WJ',  " WJetsToLNuHT800to1200", "W + jets", 5.366*1.166 ),
    ('WJ', " WJetsToLNuHT1200to2500", "W + jets", 1.074*1.166 ),
    ('WToMuNu',            "WToMuNu",  "WToMuNu", 1.0*7.273   ),
    ('WToTauNu',          "WToTauNu", "WToTauNu", 1.0*7.246   ),
  ]
  datasamples = { # table of data samples (per channel) to be converted to Sample objects
    'munu': ('Data', "SingleMuon_Run%d?"%era, 'Observed'),
  }
  
  # SAMPLE SET
  sampleset = getsampleset(datasamples,expsamples,channel=channel,era=era,file=fname,weight=weight)
  #sampleset.stitch("W*Jets", incl='WJ', name='WJ')
  sampleset.join('WJ', name='WJ', tile = 'W*Jets')  
  sampleset.printtable()
  return sampleset
  

def plotSampleSet(channel,sampleset,tag="",outdir="plots"):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plotSampleSet")
  
  selections = [
    'njets == 0 && met > 120 && pt_1 > 120 && DPhi>2.6 && nmuons ==1 && nelec == 0',
  ]
  variables = [
    Var('mt_1', "mt(mu,MET)",                                                               100,  0, 400),
    Var('pt_1', "Muon pt"   ,                                                               100,  0, 400),
    Var('met' , "MET pt"    ,                                                               100,  0, 400),
    Var('DPhi', "Azymuthal angular difference between Muon pt and MET", 100, -3.1415926538, 3.1415926538),
  ]
  text = "#mu#nu_{h} baseline" 
  
  # PLOT
  outdir   = ensuredir(outdir)
  parallel = True #and False
  fname    = "%s/plotPico_$VAR%s"%(outdir,tag)
  for selection in selections:
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',parallel=parallel)
    for stack, variable in stacks.iteritems():
      #position = "" #variable.position or 'topright'
      stack.draw()
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=['png','pdf'])
      stack.close()

def main():
  channel = 'munu'
  era     = 2018
  fname   = "$PICODIR/$SAMPLE_$CHANNEL.root"
  setera(era)
  sampleset = makesamples(channel,era,fname)
  plotSampleSet(channel,sampleset,tag="",outdir="plots")
  

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Plotting script for W*toMuNu analysis """
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print "\n>>> Done."
  
