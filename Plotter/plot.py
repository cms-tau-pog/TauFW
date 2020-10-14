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
  baseline  = "(q_1*q_2<0) && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
  selections = [
#     Sel('baseline, no DeepTauVSjet',baseline.replace(" && idDeepTau2017v2p1VSjet_2>=16","")),
    Sel('baseline',baseline),
    #Sel('zttregion',repkey(zttregion,WP=16)),
  ]
  
  # VARIABLES
  variables = [
#     Var('pt_1',  "Muon pt",    40,  0, 120, ctitle={'etau':"Electron pt",'tautau':"Leading tau_h pt",'emu':"Electron pt"}),
#     Var('pt_2',  "tau_h pt",   40,  0, 120, ctitle={'tautau':"Subleading tau_h pt",'emu':"Muon pt"}),
#     Var('eta_1', "Muon eta",   30, -3, 3, ctitle={'etau':"Electron eta",'tautau':"Leading tau_h eta",'emu':"Electron eta"},ymargin=1.6,pos='T',ncols=2),
#     Var('eta_2', "tau_h eta",  30, -3, 3, ctitle={'etau':"Electron eta",'tautau':"Subleading tau_h eta",'emu':"Muon eta"},ymargin=1.6,pos='T',ncols=2),
#     Var('m_vis',  40,  0, 200),
#     Var('mt_1',  "mt(mu,MET)", 40,  0, 200),
#     Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"]),
#     Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"]),
#     Var("jeta_1", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
#     Var("jeta_2", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
#     Var('njets',   8,  0,   8),
#     Var('met',    50,  0, 150),
#     Var('pt_ll',   "p_{T}(mutau_h)", 25, 0, 200, ctitle={'etau':"p_{T}(etau_h)",'tautau':"p_{T}(tau_htau_h)",'emu':"p_{T}(emu)"}),
#     Var('dR_ll',   "DR(mutau_h)",    30, 0, 6.0, ctitle={'etau':"DR(etau_h)",'tautau':"DR(tau_htau_h)",'emu':"DR(emu)"}),
#     Var('deta_ll', "deta(mutau_h)",  20, 0, 6.0, ctitle={'etau':"deta(etau_h)",'tautau':"deta(tautau)",'emu':"deta(emu)"},logy=True,pos='TRR'), #, ymargin=8, logyrange=2.6
#     Var('dzeta',  56, -180, 100, pos='L;y=0.88',units='GeV'),
    #Var("pzetavis", 50,    0, 200 ),
    Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 100, 0.0, 1, ncols=2,pos='L;y=0.85',logy=True,ymargin=2.5),
#     Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 20, 0.80, 1, fname="$VAR_zoom",ncols=2,pos='L;y=0.85'),
#     Var('rawDeepTau2017v2p1VSe_2',   "rawDeepTau2017v2p1VSe",   30, 0.70, 1, fname="$VAR_zoom",ncols=2,logy=True,pos='L;y=0.85'),
#     Var('rawDeepTau2017v2p1VSmu_2',  "rawDeepTau2017v2p1VSmu",  20, 0.80, 1, fname="$VAR_zoom",ncols=2,logy=True,logyrange=4,pos='L;y=0.85'),
#     Var('npv',    40,    0,  80 ),
  ]
  
  # PLOT
  outdir   = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  exts     = ['png','pdf'] if pdf else ['png'] # extensions
  for selection in selections:
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',parallel=parallel)
    fname  = "%s/$VAR_%s-%s-%s$TAG"%(outdir,channel,selection.filename,era)
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
  outdir   = "plots/$ERA"
  tag      = ""
  fname    = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style and lumi-xsec normalization
      sampleset = getsampleset(channel,era,fname=fname)
      plot(sampleset,channel,parallel=parallel,tag="",outdir=outdir,era=era,pdf=pdf)
  

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
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  


