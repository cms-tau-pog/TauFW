#! /usr/bin/env python
# Author: Izaak Neutelings (July 2020)
# Description: Create 2D histograms for individual samples
#   ./plot2D.py -c mutau -y UL2018 -s DY
from config.samples import *
from TauFW.Plotter.plot.string import filtervars
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Plotter.plot.Plot2D import Plot2D

  
def plot2D(samples,channel,parallel=True,tag="",extratext="",outdir="plots",era="",
           varfilter=None,selfilter=None,pdf=False,verb=0):
  """Plot 2D histogram."""
  LOG.header("plot2D")
  
  # SELECTIONS
  if 'mutau' in channel:
    baseline  = "q_1*q_2<0 && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  elif 'etau' in channel:
    baseline  = "q_1*q_2<0 && iso_1<0.10 && mvaFall17noIso_WP90_1 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
  else:
    baseline  = "q_1*q_2<0 && iso_1<0.15 && iso_2<0.15 && idMedium_1 && idMedium_2 && !extraelec_veto && !extramuon_veto && m_ll>20 && metfilter"
  zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
  selections = [
    #Sel('baseline, no DeepTauVSjet',baseline.replace(" && idDeepTau2017v2p1VSjet_2>=16","")),
    Sel("baseline",baseline),
    #Sel("baseline, pt > 29 GeV",baseline+" && pt_1>29 GeV && pt_1>20 GeV"),
    #Sel("mt<60 GeV, dzeta>-25 GeV, |deta|<1.5",zttregion,fname="zttregion"),
  ]
  selections = filtervars(selections,selfilter) # filter variable list with -V flag
  
  pt_1 = Var('pt_1',  "Muon pt",    40,  0, 120, ctitle={'etau':"Electron pt",'tautau':"Leading tau_h pt",'mumu':"Leading muon pt",'emu':"Electron pt"})
  pt_2 = Var('pt_2',  "tau_h pt",   40,  0, 120, ctitle={'tautau':"Subleading tau_h pt",'mumu':"Subleading muon pt",'emu':"Muon pt"})
  vars2D = [
   (pt_1,pt_2),
   (Var('met',"PF MET",50,0,200,opts={'prof':True}),Var('met-genmet',"PF MET - gen. MET",40,-30,90)),
  ]
  #vars2D = filtervars(variables,varfilter) # filter variable list with -V flag
  
  # PLOT
  outdir  = ensuredir(repkey(outdir,CHANNEL=channel,ERA=era))
  chshort = channel.replace('ele','e').replace('mu','m').replace('tau','t')
  ztitle  = "Events"
  for sample in samples:
    header = sample.title
    sname  = sample.name
    LOG.color(sample.title,b=True,ul=True)
    for selection in selections:
      text  = "%s: %s"%(channel.replace("tau","tau_{h}"),selection.title)
      fname = "%s/plot2D_$VAR_%s_%s-%s%s$TAG"%(outdir,sname,chshort,selection.filename,tag)
      hists = sample.gethist2D(vars2D,selection,parallel=parallel)
      for (xvar, yvar), hist in zip(vars2D,hists):
        rho = hist.GetCorrelationFactor()
        text_ = "%s\n#rho = %.2f"%(text,rho)
        print ">>> rho = %.2f for %s vs. %s"%(rho,yvar.name,xvar.name,)
        plot = Plot2D(xvar,yvar,hist)
        plot.draw(ztitle=ztitle,logz=True,verb=verb) #zmin=1e-2,zmax=4e1
        plot.drawtext(text_,size=0.052)
        if xvar.opts.get('prof',False) or yvar.opts.get('prof',False):
          plot.drawprofile('x')
        plot.saveas(fname,ext=['png'],tag=tag) #,'pdf'
        plot.close()
  

def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel and False
  varfilter = args.varfilter
  selfilter = args.selfilter
  samfilter = args.samfilter or ["DY"]
  tag       = args.tag
  extratext = args.text
  pdf       = args.pdf
  verbosity = args.verbosity
  outdir    = "plots/$ERA"
  fname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  for era in eras:
    for channel in channels:
      setera(era) # set era for plot style and lumi-xsec normalization
      sampleset = getsampleset(channel,era,fname=fname)
      samples = sampleset.get(samfilter,verb=verbosity)
      plot2D(samples,channel,parallel=parallel,tag=tag,extratext=extratext,
             outdir=outdir,era=era,varfilter=varfilter,selfilter=selfilter,pdf=pdf)
      sampleset.close()
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  channels = ['mutau','etau','mumu']
  eras = ['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018']
  argv = sys.argv
  description = """Simple plotting script for 2D histograms from pico analysis tuples"""
  parser = ArgumentParser(prog="plot",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['UL2017'],
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=channels, default=['mutau'],
                                         help="set channel" )
  parser.add_argument('-V', '--var',     dest='varfilter', nargs='+',
                                         help="only plot the variables passing this filter (glob patterns allowed)" )
  parser.add_argument('-S', '--sel',     dest='selfilter', nargs='+',
                                         help="only plot the selection passing this filter (glob patterns allowed)" )
  parser.add_argument('-s', '--sample',  dest='samfilter', nargs='+',
                                         help="only plot the samples passing this filter (glob patterns allowed)" )
  parser.add_argument('--serial',        dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-p', '--pdf',     dest='pdf', action='store_true',
                                         help="create pdf version of each plot" )
  parser.add_argument('-t', '--tag',     default="", help="extra tag for output" )
  parser.add_argument('-T', '--text',    default="", help="extra text on plot" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
