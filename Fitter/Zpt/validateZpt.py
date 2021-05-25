#! /usr/bin/env python
# Author: Izaak Neutelings (January 2021)
# Description: Script to measure Z pt reweighting based on dimuon events
#   ./measureZpt.py -y 2018
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.common.tools.math import frange
from ROOT import gROOT
gROOT.Macro('weights/zptweight.C+')
from ROOT import loadZptWeights

baseline = "q_1*q_2<0 && iso_1<0.15 && iso_1<0.15 && !extraelec_veto && !extramuon_veto && m_vis>20"
Zmbins0  = [20,70,91,110,150,200,300,400,500,600,700,800,900,1000]
Zmbins1  = [20,30,40,50,60,70,80,85,88,89,89.5,90,90.5,91,91.5,92,93,94,95,100,110,120,180,500,1000]
Zmbins2  = [20,30,40,50,60,70,80,85,86,87,88,88.5,89,89.5,90,90.5,91,91.5,92,92.5,93,94,95,100,110,120,180,250,500,1000]
Zmbins3  = [200,300,400,500,600,700,800,900,1000,1200,1500,2000]
ptbins0  = [0,10,20,30,50,70,100,140,190,250,300,500,700,1000]
ptbins1  = [0,2,4,6,8,10,12,15,20,30,40,50,60,70,80,90,100,120,140,160,180,200,225,250,350,500,1000]
dRbins   = [0,0.4,1.0,1.5,2.0]+frange(2.2,5.61,0.2)+[6.0]
print dRbins


def plot(era,channel,weight="",tag="",outdir="plots",parallel=True,pdf=False):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot %s"%(tag.strip('_')))
  
  # ERA
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  dyweight  = weight #"zptweight"
  #sampleset = getsampleset(channel,era,fname=fname,dyweight="")
  sampleset = getsampleset(channel,era,fname=fname,dyweight=weight,dy="mass")
  #sampleset = getsampleset(channel,era,fname=fname,dyweight=dyweight)
  
  # SELECTIONS
  selections = [
    Sel('baseline',                         baseline),
    #Sel('m_{mumu} > 200 GeV',               baseline+" && m_vis>200", fname="mgt200"),
    #Sel('0j, m_{mumu} > 200 GeV',           baseline+" && m_vis>200 && njets50==0", fname="0j-mgt200"),
    #Sel('0j, 200 GeV < m_{mumu} < 400 GeV', baseline+" && m_vis>200 && m_vis<400 && njets50==0", fname="0j-mgt200-400"),
  ]
  
  # VARIABLES
  variables = [
    Var('pt_1',  "Leading muon pt",     40,  0,  120, cbins={"m_vis>200":(25,20,270)} ),
    Var('pt_2',  "Subleading muon pt",  40,  0,  120, cbins={"m_vis>200":(25,20,270)} ),
    Var('eta_1', "Leading muon eta",    30, -3,    3, ymargin=1.6, pos='T', ncols=2),
    Var('eta_2', "Subleading muon eta", 30, -3,    3, ymargin=1.6, pos='T', ncols=2),
    Var('m_ll',  "m_mumu",              40,  0,  200, fname="$VAR", cbins={"m_vis>200":(40,200,1000)}), # alias: m_ll alias of m_vis
    Var('m_ll',  "m_mumu",              40,  0,  200, fname="$VAR_log", logy=True, cbins={"m_vis>200":(40,200,1000)} ),
    Var('m_ll',  "m_mumu",              40, 70,  110, fname="$VAR_Zmass", veto=["m_vis>200"] ),
    Var('m_ll',  "m_mumu",              Zmbins0,      fname="$VAR_tail", logy=True, logyrange=6, cbins={"m_vis>200":Zmbins3} ),
    #Var('mt_1',  "mt(mu,MET)", 40,  0, 200),
    #Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"]),
    #Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"]),
    #Var("jeta_1", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    #Var("jeta_2", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var('njets',   8,  0,   8),
    #Var('met',    50,  0, 150),
    Var('pt_ll',   "pt(mumu)",    25, 0, 200, cbins={"m_vis>200":ptbins0}),
    Var('pt_ll',   "pt(mumu)",    25, 0, 200, fname="$VAR_log", logy=True, logx=True, cbins={"m_vis>200":ptbins0}),
    Var('dR_ll',   "DR(mumu)",    30, 0, 6.0 ),
    Var('dR_ll',   "DR(mumu)",    dRbins, fname="$VAR_log", logy=True, pos='Ly=0.88', logyrange=7),
    Var('deta_ll', "deta(mumu)",  20, 0, 6.0, logy=True, pos='TRR'), #, ymargin=8, logyrange=2.6
    #Var('dzeta',  56, -180, 100, pos='L;y=0.88',units='GeV'),
    #Var("pzetavis", 50,    0, 200 ),
    #Var('npv',    40,    0,  80 ),
  ]
  
  # PLOT
  outdir   = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  exts     = ['png','pdf'] if pdf else ['png'] # extensions
  for selection in selections:
    stacks = sampleset.getstack(variables,selection,method='QCD_OSSS',parallel=parallel)
    fname  = "%s/$VAR_%s-%s-%s$TAG"%(outdir,channel.replace('mu',"m"),selection.filename,era)
    text   = "%s: %s"%(channel.replace('mu',"#mu").replace('tau',"#tau_{h}"),selection.title)
    for stack, variable in stacks.iteritems():
      #position = "" #variable.position or 'topright'
      stack.draw()
      stack.drawlegend() #position)
      stack.drawtext(text)
      stack.saveas(fname,ext=exts,tag=tag)
      stack.close()
  
  sampleset.close()
  

def main(args):
  channels = args.channels
  eras     = args.eras
  parallel = args.parallel
  pdf      = args.pdf
  outdir   = "plots/$ERA"
  tag      = ""
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style and lumi-xsec normalization
      plot(era,channel,weight="",                     tag="_noweight",  outdir=outdir,parallel=parallel,pdf=pdf)
      #loadZptWeights("0j-mgt200_"+era,"zpt_weight_reco")
      #plot(era,channel,weight="getZptWeight(pt_ll)",  tag="_recoweight",outdir=outdir,parallel=parallel,pdf=pdf)
      loadZptWeights(era,"zpt_weight")
      #loadZptWeights("0j-mgt200_"+era,"zpt_weight")
      plot(era,channel,weight="getZptWeight(pt_moth)",tag="_genweight", outdir=outdir,parallel=parallel,pdf=pdf)
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mumu'], default=['mumu'], action='store',
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
  
