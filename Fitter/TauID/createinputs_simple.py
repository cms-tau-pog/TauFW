#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs_simple.py -c mutau -y UL2017
import sys
from collections import OrderedDict
sys.path.append("../../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Plotter.plot.datacard import createinputs, plotinputs



def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt_simple' # $PROCESS_$ANALYSIS
  tag       = ""
  
  for era in eras:
    for channel in channels:
      
      
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations
      
      # GET SAMPLESET
      join       = ['VV','TT','ST']
      sname      = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset  = getsampleset(channel,era,fname=sname,join=join,split=None,table=False)
      
      # SPLIT & RENAME (HTT convention)
      GMR = "genmatch_2==5"
      GML = "genmatch_2>0 && genmatch_2<5"
      GMJ = "genmatch_2==0"
      sampleset.split('DY',[('ZTT',GMR),('ZL',GML),('ZJ',GMJ),])
      sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
      sampleset.rename('WJ','W')
      sampleset.datasample.name = 'data_obs'
      
      # SYSTEMATIC VARIATIONS
      varprocs = OrderedDict([ # processes to be varied
        ('Nom',     ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
        #('TESUp',   ['ZTT','TTT']),
        #('TESDown', ['ZTT','TTT']),
      ])
      samplesets = { # sets of samples per variation
        'Nom':     sampleset, # nominal
        #'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p030","_TESUp",  " +3% TES", split=True,filter=False,share=True),
        #'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p970","_TESDown"," -3% TES", split=True,filter=False,share=True),
      }
      for shift in ['Nom','TESUp','TESDown']:
        if not shift in samplesets: continue
        samplesets[shift].printtable(merged=True,split=True)
        if verbosity>=2:
          samplesets[shift].printobjs(file=True)
      
      
      ###################
      #   OBSERVABLES   #
      ###################
      # observable/variables to be fitted in combine
      observables = [
        Var('m_vis', 30, 50, 200),
        #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
      ]
      
      
      ############
      #   BINS   #
      ############
      # selection categories
      iso_1     = "iso_1<0.15"
      iso_2     = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
      baseline  = "q_1*q_2<0 && %s && %s && !lepton_vetoes_notau && metfilter"%(iso_1,iso_2)
      bins = [
        Sel('baseline',baseline),
      ]
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      createinputs(fname,samplesets['Nom'],    observables,bins,recreate=True)
      #createinputs(fname,samplesets['TESUp'],  observables,bins,filter=varprocs['TESUp']  )
      #createinputs(fname,samplesets['TESDown'],observables,bins,filter=varprocs['TESDown'])
      
      
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
        text   = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups = [ ] #(['^TT','ST'],'Top'),]
        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups)
      


if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['UL2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau'], default=['mutau'], action='store',
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
  

