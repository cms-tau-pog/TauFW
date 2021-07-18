#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Simple plotting script for pico analysis tuples
#   ./plot.py -c mutau -y 2018
from config.samples import *
from TauFW.Plotter.plot.string import filtervars
from TauFW.Plotter.plot.utils import LOG as PLOG


def plot(sampleset,channel,parallel=True,tag="",outdir="plots",era="",varfilter=None,selfilter=None,pdf=False):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("plot")
  
  # SELECTIONS
  if 'mutau' in channel:
    baseline  = "q_1*q_2<0 && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  elif 'etau' in channel:
    baseline  = "q_1*q_2<0 && iso_1<0.10 && mvaFall17noIso_WP90_1 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  else:
    baseline  = "q_1*q_2<0 && iso_1<0.15 && iso_2<0.15 && !extraelec_veto && !extramuon_veto && m_ll>20 && metfilter"
  zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
  selections = [
    #Sel('baseline, no DeepTauVSjet',baseline.replace(" && idDeepTau2017v2p1VSjet_2>=16","")),
    Sel("baseline",baseline),
    #Sel("mt<60 GeV, dzeta>-25 GeV, |deta|<1.5",zttregion,fname="zttregion"), #repkey(zttregion,WP=16)
  ]
  selections = filtervars(selections,selfilter) # filter variable list with -V flag
  
  # VARIABLES
  variables = [
    Var('pt_1',  "Muon pt",    40,  0, 120, ctitle={'etau':"Electron pt",'tautau':"Leading tau_h pt",'emu':"Electron pt"}),
    Var('pt_2',  "tau_h pt",   40,  0, 120, ctitle={'tautau':"Subleading tau_h pt",'emu':"Muon pt"}),
    Var('eta_1', "Muon eta",   30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Leading tau_h eta",'emu':"Electron eta"},ymargin=1.6,pos='T',ncols=2),
    Var('eta_2', "tau_h eta",  30, -3,   3, ctitle={'etau':"Electron eta",'tautau':"Subleading tau_h eta",'emu':"Muon eta"},ymargin=1.6,pos='T',ncols=2),
    Var('mt_1',  "mt(mu,MET)", 40,  0, 200, ctitle={'etau':"mt(mu,MET)",'tautau':"mt(tau,MET)",'emu':"mt(e,MET)"}),
    Var("jpt_1",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jpt_2",  29,   10,  300, veto=[r"njets\w*==0"]),
    Var("jeta_1", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var("jeta_2", 53, -5.4,  5.2, ymargin=1.6,pos='T',ncols=2,veto=[r"njets\w*==0"]),
    Var('npv',    40,  0,  80 ),
    Var('njets',   8,  0,   8),
    Var('met',    50,  0, 150),
    Var('pt_ll',   "p_{T}(mutau_h)", 25, 0, 200, ctitle={'etau':"p_{T}(etau_h)",'tautau':"p_{T}(tau_htau_h)",'emu':"p_{T}(emu)"}),
    Var('dR_ll',   "DR(mutau_h)",    30, 0, 6.0, ctitle={'etau':"DR(etau_h)",'tautau':"DR(tau_htau_h)",'emu':"DR(emu)"}),
    Var('deta_ll', "deta(mutau_h)",  20, 0, 6.0, ctitle={'etau':"deta(etau_h)",'tautau':"deta(tautau)",'emu':"deta(emu)"},logy=True,pos='TRR',cbins={"abs(deta_ll)<":(10,0,3)}), #, ymargin=8, logyrange=2.6
    Var('dzeta',  56, -180, 100, pos='L;y=0.88',units='GeV'),
  ]
  if 'tau' in channel:
    loadmacro("python/macros/mapDecayModes.C") # for mapRecoDM
    dmlabels  = ["h^{#pm}","h^{#pm}h^{0}","h^{#pm}h^{#mp}h^{#pm}","h^{#pm}h^{#mp}h^{#pm}h^{0}","Other"]
    variables += [
      Var("dm_2",           14,  0,  14, fname="dm_2",title="Reconstructed tau_h decay mode",veto="dm_2==",position="TT",ymargin=1.2),
      Var("mapRecoDM(dm_2)", 5,  0,   5, fname="dm_2_label",title="Reconstructed tau_h decay mode",veto="dm_2==",position="TT",labels=dmlabels,ymargin=1.2),
      #Var("pzetavis", 50,    0, 200 ),
      Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 100, 0.0, 1, ncols=2,pos='L;y=0.85',logy=True,ymargin=1.5,cbins={"VSjet_2>":(60,0.4,1)}),
      Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 20, 0.80, 1, fname="$VAR_zoom",ncols=2,pos='L;y=0.85'),
      Var('rawDeepTau2017v2p1VSe_2',   "rawDeepTau2017v2p1VSe",   30, 0.70, 1, fname="$VAR_zoom",ncols=2,logy=True,logyrange=4,pos='L;y=0.85'),
      Var('rawDeepTau2017v2p1VSmu_2',  "rawDeepTau2017v2p1VSmu",  20, 0.80, 1, fname="$VAR_zoom",ncols=2,logy=True,logyrange=5,pos='L;y=0.85'),
      Var('m_vis',  40,  0, 200, ctitle={'mumu':"m_mumu",'emu':"m_emu"}),
    ]
  elif channel=='mumu':
    variables += [
      Var('m_ll', "m_mumu", 40,  0,  200, fname="$VAR", cbins={"m_vis>200":(40,200,1000)}), # alias: m_ll alias of m_vis
      Var('m_ll', "m_mumu", 40,  0,  200, fname="$VAR_log", logy=True, ymin=1e2, cbins={"m_vis>200":(40,200,1000)} ),
      Var('m_ll', "m_mumu", 40, 70,  110, fname="$VAR_Zmass", veto=["m_vis>200"] ),
    ]
  variables = filtervars(variables,varfilter) # filter variable list with -V flag
  
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
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  varfilter = args.varfilter
  selfilter = args.selfilter
  tag       = args.tag
  pdf       = args.pdf
  outdir    = "plots/$ERA"
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style and lumi-xsec normalization
      sampleset = getsampleset(channel,era,fname=fname)
      plot(sampleset,channel,parallel=parallel,tag=tag,outdir=outdir,era=era,
           varfilter=varfilter,selfilter=selfilter,pdf=pdf) #,dyweight="")
      sampleset.close()
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  channels = ['mutau','etau','mumu']
  eras = ['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018']
  argv = sys.argv
  description = """Simple plotting script for pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['2017'],
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=channels, default=['mutau'],
                                         help="set channel" )
  parser.add_argument('-V', '--var',     dest='varfilter', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilter', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-t', '--tag',     default="", help="extra tag for output" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
