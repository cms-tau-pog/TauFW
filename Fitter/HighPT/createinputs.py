#! /usr/bin/env python
# Author: Jacopo Malvaso (August 2022)
# Description: Create input histograms for datacards
#   ./createinputs.py -c munu -y 2018
#copiato da TauID 
import sys
sys.path.append("../../Plotter/") # for config.samples
from config.samples_HighPT import *
from TauFW.Plotter.plot.utils import LOG as PLOG 
from TauFW.Plotter.plot.utils import ensuredir
from TauFW.Fitter.plot.datacard import createinputs, plotinputs, preparesysts


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  analysis  = "munu" # $PROCESS_$ANALYSIS
  tag       = ""
  fileexp   = "$OUTDIR/$ANALYSIS_$OBS_$CHANNEL-$ERA$TAG.inputs.root"
  outdir    = ensuredir("input")
  plotdir   = "input/plots/$ERA"
  
  for era in eras:
    for channel in channels:
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations

      # GET SAMPLESET
      join      = ['WJ']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset = getsampleset(channel,era,fname=sname,join=join)
        
      # RENAME (HTT convention)
      sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
      samplesets = { # sets of samples per variation
          'Nom': sampleset, # nominal
        }
      systs = preparesysts( # prepare systematic variations: syskey, systag, procs
          ('Nom',"",  ['WToMuNu','WJ','data_obs']),
        )
      samplesets['Nom'].printtable(merged=True,split=True)
      if verbosity>=2:
        samplesets['Nom'].printobjs(file=True)
      
      samplesets = { # create new sets of samples per energy scale variation
          'Nom':     sampleset, # nominal
        #  'MESUp':   sampleset.shift(systs['MES'].procs,"_MES1p01",systs['MES'].up," +1% MES", split=True,filter=False,share=True),
        #  'MESDown': sampleset.shift(systs['MES'].procs,"_MES0p99",systs['MES'].dn," -1% MES", split=True,filter=False,share=True)
      }

      ###################
      #   OBSERVABLES   #
      ###################
      # observable/variables to be fitted in combine
      
      observables = [
        Var('mt_1', "m_{T}(#mu,MET)", 100,  50, 750, fname='mt_1', ymargin=1.6, rrange=0.16),
        Var('pt_1', "Muon p_{T}"   ,  100,  50, 400, fname='pt_1', ymargin=1.6, rrange=0.16),
        Var('met' , "MET p_{T}"    ,  100, 50, 400, fname='met', ymargin=1.6, rrange=0.16),
        Var('DPhi', "#Delta#phi(#mu,MET)", 100, -3.15, 3.15, fname='DPhi', ymargin=1.6, rrange=0.16),
        ]
      
      ############
      #   BINS   #
      ############
      # selection categories
      
      if channel=='munu':
        
        baseline = "njets==0 && met > 120 && pt_1 > 110 && abs(DPhi) > 2.6 && extramuon_veto < 0.5 &&  extraelec_veto < 0.5"
        bins = [
          Sel('WToMuNu', "W* -> #mu#nu", baseline),
        ]
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      chshort = channel.replace('mu','#mu') # abbreviation of channel
      fname   = repkey(fileexp,OUTDIR=outdir,ANALYSIS=analysis,CHANNEL=chshort,ERA=era,TAG=tag)
      createinputs(fname,samplesets['Nom'],observables,bins,recreate=True)
  
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      if plot:
        plotdir_ = ensuredir(repkey(plotdir,ERA=era,CHANNEL=channel))
        pname    = repkey(fileexp,OUTDIR=plotdir_,ANALYSIS=analysis,CHANNEL=chshort+"-$BIN",ERA=era,TAG='$TAG'+tag).replace('.root','.png')
        text     = "%s: $BIN"%(channel.replace("mu","#mu").replace("nu","#nu"))
        groups   = [ ] 
        plotinputs(fname,systs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups)
      
if __name__ == "__main__":
  from argparse import ArgumentParser
  eras = ['2016','2017','2018']
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['2018'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['munu'], default=['munu'], action='store',
                                         help="set channel" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
