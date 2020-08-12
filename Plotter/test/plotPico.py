#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Simple plotting script for pico analysis tuples
#   test/plotPico.py -v2
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, setera, ensuredir,\
                                       getsampleset, Var

def makesamples(channel,era,fname):
  LOG.header("makesamples")
  weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2" 
  expsamples = [ # table of MC samples to be converted to Sample objects
    ('DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
    ('DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
    ('DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
    ('DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
    ('DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
    ('DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
    ('WJ', "WJetsToLNu",            "W + jets",           50260.0, ),
    ('WJ', "W1JetsToLNu",           "W + 1J",              9625.0  ),
    ('WJ', "W2JetsToLNu",           "W + 2J",              3161.0  ),
    ('WJ', "W3JetsToLNu",           "W + 3J",               954.8  ),
    ('WJ', "W4JetsToLNu",           "W + 4J",               494.6  ),
    ('VV', "WW",                    "WW",                    75.88 ),
    ('VV', "WZ",                    "WZ",                    27.6  ),
    ('VV', "ZZ",                    "ZZ",                    12.14 ),
    ('ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
    ('ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
    ('ST', "ST_tW_top",             "ST tW",                 35.85 ),
    ('ST', "ST_tW_antitop",         "ST atW",                35.85 ),
    ('TT', "TT",                    "ttbar",                831.76, {'extraweight': 'ttptweight'} ),
  ]
  datasamples = { # table of data samples (per channel) to be converted to Sample objects
    'mutau': ('Data', "SingleMuon_Run%d?"%era, 'Observed'),
    'etau':  ('Data', "SingleElectron_Run%d?"%era),
  }
  
  # SAMPLE SET
  sampleset = getsampleset(datasamples,expsamples,channel=channel,era=era,file=fname,weight=weight)
  sampleset.stitch("W*Jets",    incl='WJ',  name='WJ'     ) #title="W + jets"
  sampleset.stitch("DY*J*M-50", incl='DYJ', name="DY_M50" ) #title="Drell-Yan, M > 50 GeV"
  #sampleset.stitch("DY*J*M-10to50", incl='DYJ', name="DY_M10to50" )
  sampleset.join('DY',                name='DY'  ) #title="Drell-Yan"           
  sampleset.join('VV','WZ','WW','ZZ', name='VV'  ) #title="Diboson"             
  sampleset.join('TT','ST',           name='Top' ) #title="ttbar and single top"
  sampleset.split('DY',[
    ('ZTT',"Z -> tau_{#mu}tau_{h}",      "genmatch_2==5"),
    ('ZL', "Drell-Yan with l -> tau_{h}","genmatch_2>0 && genmatch_2<5"),
    ('ZJ', "Drell-Yan with j -> tau_{h}","genmatch_2==0")
  ])
  sampleset.printtable()
  return sampleset
  

def plotSampleSet(channel,sampleset,tag="",outdir="plots"):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plotSampleSet")
  
  selections = [
    'q_1*q_2<0 && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter',
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
  channel = 'mutau'
  era     = 2016
  fname   = "$PICODIR/$SAMPLE_$CHANNEL.root"
  setera(era)
  sampleset = makesamples(channel,era,fname)
  plotSampleSet(channel,sampleset,tag="",outdir="plots")
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  main()
  print "\n>>> Done."
  
