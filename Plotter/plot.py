#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Simple plotting script for pico analysis tuples
#   ./plot.py -c mutau -y 2018
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG


def plot(sampleset,channel,parallel=True,tag="",outdir="plots",era="",pdf=False):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot")
  
  # SELECTIONS
  baseline  = "q_1*q_2<0 && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
  selections = [
    Sel('baseline',baseline),
    #Sel('zttregion',repkey(zttregion,WP=16)),
  ]
  
  # VARIABLES
  variables = [
    Var('pt_1',  "Muon pt",    40,  0, 120),
    Var('pt_2',  "tau_h pt",   40,  0, 120),
    Var('eta_1', "Muon eta",   30, -3, 3, ymargin=1.5, ncols=2),
    Var('eta_2', "tau_h eta",  30, -3, 3, ymargin=1.5, ncols=2),
    Var('m_vis',  40,  0, 200),
    Var('mt_1',  "mt(mu,MET)", 40,  0, 200),
    Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"] ),
    Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"] ),
    Var("jeta_1", 53, -5.4,  5.2, pos='LL', ymargin=1.5, ncols=2, veto=[r"njets\w*==0"] ),
    Var("jeta_2", 53, -5.4,  5.2, pos='LL', ymargin=1.5, ncols=2, veto=[r"njets\w*==0"] ),
    Var('njets',   8,  0,   8),
    Var('met',    50,  0, 150),
    Var('pt_ll',   "p_{T}(mutau_h)", 30, 0, 450, ctitle={'etau':"p_{T}(etau_h)",'tautau':"p_{T}(tau_{h}tau_{h})",'emu':"p_{T}(emu)"} ),
    Var('dR_ll',   "DR_{mutau_h}",   30, 0, 6.0, ctitle={'etau':"DR_etau_h",'tautau':"DR_tautau",'emu':"DR_emu"}, pos='leftleft'),
    Var('deta_ll', "deta(mu,tau)",   20, 0,  10, ctitle={'etau':"deta(e,tau)",'tautau':"deta(tau,tau)",'emu':"deta(e,mu)"}, logy=True, ymargin=8, logyrange=2.6 ),
    Var('dzeta',  52, -160, 100, pos='x=0.07', units='GeV' ),
    #Var("pzetavis", 50,    0, 200 ),
    Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 100, 0.0, 1, ncols=2, pos='L;y=0.88', logy=True, ymargin=2.5),
    Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 22, 0.78, 1, fname="$VAR_zoom", ncols=2, pos='L;y=0.88'),
    Var('rawDeepTau2017v2p1VSe_2',   "rawDeepTau2017v2p1VSe",   22, 0.78, 1, fname="$VAR_zoom", ncols=2, pos='L;y=0.88'),
    Var('rawDeepTau2017v2p1VSmu_2',  "rawDeepTau2017v2p1VSmu",  22, 0.78, 1, fname="$VAR_zoom", ncols=2, pos='L;y=0.88'),
    Var('npv',    40,    0,  80 ),
    
  ]
  
  # PLOT
  outdir   = ensuredir(outdir)
  exts     = ['png','pdf'] if pdf else ['png']
  for selection in selections:
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',parallel=parallel)
    fname  = "%s/plot_$VAR_%s-%s-%s$TAG"%(outdir,channel,selection.filename,era)
    text   = "%s: %s"%(channel.replace('mu',"#mu").replace('tau',"#tau_{h}"),selection.title)
    for stack, variable in stacks.iteritems():
      #position = "" #variable.position or 'topright'
      stack.draw()
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=exts,tag=tag)
      stack.close()
  

def main(args):
  channels = args.channels
  eras     = args.eras
  parallel = args.parallel
  pdf      = args.pdf
  outdir   = "plots"
  tag      = ""
  fname    = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style and lumi-xsec normalization
      sampleset = getsampleset(channel,era,fname=fname)
      plot(sampleset,channel,parallel=parallel,tag="",outdir=outdir,era=era)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau'], default=['mutau'], action='store',
                                         help="set channel" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_false',
                                         help="create pdf version of each plot" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
