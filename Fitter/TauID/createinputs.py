#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py -c mutau -y UL2017
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
  analysis  = 'ztt_tid' # $PROCESS_$ANALYSIS
  tag       = ""
  
  for era in eras:
    for channel in channels:
      
      
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations
      
      # GET SAMPLESET
      join      = ['VV','TT','ST']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset = getsampleset(channel,era,fname=sname,join=join,split=None,table=False)
      
      if channel=='mumu':
        
        # RENAME (HTT convention)
        sampleset.rename('DY_M50','ZLL')
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        varprocs = { # processes to be varied
          'Nom': ['ZLL','W','VV','ST','TT','QCD','data_obs'],
        }
        samplesets = { # sets of samples per variation
          'Nom': sampleset, # nominal
        }
        samplesets['Nom'].printtable(merged=True,split=True)
        if verbosity>=2:
          samplesets['Nom'].printobjs(file=True)
      
      else:
        
        # SPLIT & RENAME (HTT convention)
        GMR = "genmatch_2==5"
        GML = "genmatch_2>0 && genmatch_2<5"
        GMJ = "genmatch_2==0"
        GMF = "genmatch_2<5"
        sampleset.split('DY',[('ZTT',GMR),('ZL',GML),('ZJ',GMJ),])
        sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
        #sampleset.split('ST',[('STT',GMR),('STJ',GMF),]) # small background
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        varprocs = OrderedDict([ # processes to be varied
          ('Nom',     ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          ('TESUp',   ['ZTT','TTT']),
          ('TESDown', ['ZTT','TTT']),
          ('LTFUp',   ['ZL', 'TTL']),
          ('LTFDown', ['ZL', 'TTL']),
          ('JTFUp',   ['ZJ', 'TTJ', 'QCD', 'W']),
          ('JTFDown', ['ZJ', 'TTJ', 'QCD', 'W']),
        ])
        samplesets = { # sets of samples per variation
          'Nom':     sampleset, # nominal
          'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p030","_TESUp",  " +3% TES", split=True,filter=False,share=True),
          'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p970","_TESDown"," -3% TES", split=True,filter=False,share=True),
          'LTFUp':   sampleset.shift(varprocs['LTFUp'],  "_LTF1p030","_LTFUp",  " +3% LTF", split=True,filter=False,share=True),
          'LTFDown': sampleset.shift(varprocs['LTFDown'],"_LTF0p970","_LTFDown"," -3% LTF", split=True,filter=False,share=True),
          'JTFUp':   sampleset.shift(varprocs['JTFUp'],  "_JTF1p100","_JTFUp",  " +10% JTF",split=True,filter=False,share=True),
          'JTFDown': sampleset.shift(varprocs['JTFDown'],"_JTF0p900","_JTFDown"," -10% JTF",split=True,filter=False,share=True),
        }
        keys = samplesets.keys() if verbosity>=1 else ['Nom','TESUp','TESDown']
        for shift in keys:
          if not shift in samplesets: continue
          samplesets[shift].printtable(merged=True,split=True)
          if verbosity>=2:
            samplesets[shift].printobjs(file=True)
      
      
      ###################
      #   OBSERVABLES   #
      ###################
      # observable/variables to be fitted in combine
      
      if channel=='mumu':
      
        observables = [
          Var('m_vis', 1, 60, 120, ymargin=1.6, rrange=0.08),
        ]
      
      else:
        
        mvis = Var('m_vis', 30, 50, 200)
        observables = [
          Var('m_vis', 30, 50, 200),
          #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
        ]
        
        # PT & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each pt/DM bin will be a separate file
        dmbins = [0,1,10,11]
        ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        print ">>> DM cuts:"
        for dm in dmbins:
          dmcut = "pt_2>40 && dm_2==%d"%(dm)
          fname = "$VAR_dm%s"%(dm)
          mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
          print ">>>   %r (%r)"%(dmcut,fname)
          observables.append(mvis_cut)
        print ">>> pt cuts:"
        for imax, ptmin in enumerate(ptbins,1):
          if imax<len(ptbins):
            ptmax = ptbins[imax]
            ptcut = "pt_2>%s && pt_2<=%s"%(ptmin,ptmax)
            fname = "$VAR_pt%sto%s"%(ptmin,ptmax)
          else: # overflow
            #ptcut = "pt_2>%s"%(ptmin)
            #fname = "$VAR_ptgt%s"%(ptmin)
            continue # skip overflow bin
          mvis_cut = mvis.clone(fname=fname,cut=ptcut) # create observable with extra cut for pt bin
          print ">>>   %r (%r)"%(ptcut,fname)
          observables.append(mvis_cut)
      
      
      ############
      #   BINS   #
      ############
      # selection categories
      
      if channel=='mumu':
        
        baseline  = "q_1*q_2<0 && iso_1<0.15 && iso_2<0.15 && !lepton_vetoes && metfilter"
        bins = [
          Sel('ZMM', baseline),
        ]
      
      else:
        
        tauwps    = ['VVVLoose','VVLoose','VLoose','Loose','Medium','Tight','VTight','VVTight']
        tauwpbits = { wp: 2**i for i, wp in enumerate(tauwps)}
        iso_1     = "iso_1<0.15"
        iso_2     = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=$WP && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
        baseline  = "q_1*q_2<0 && %s && %s && !lepton_vetoes_notau && metfilter"%(iso_1,iso_2)
        zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
        bins = [
          #Sel('baseline', repkey(baseline,WP=16)),
          #Sel('zttregion',repkey(zttregion,WP=16)),
        ]
        for wpname in tauwps: # loop over tau ID WPs
          wpbit = tauwpbits[wpname]
          bins.append(Sel(wpname,repkey(zttregion,WP=wpbit)))
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      createinputs(fname,samplesets['Nom'],    observables,bins,recreate=True)
      if channel in ['mutau']:
        createinputs(fname,samplesets['TESUp'],  observables,bins,filter=varprocs['TESUp']  )
        createinputs(fname,samplesets['TESDown'],observables,bins,filter=varprocs['TESDown'])
        createinputs(fname,samplesets['LTFUp'],  observables,bins,filter=varprocs['LTFUp']  )
        createinputs(fname,samplesets['LTFDown'],observables,bins,filter=varprocs['LTFDown'])
        createinputs(fname,samplesets['JTFUp'],  observables,bins,filter=varprocs['JTFUp'],  htag='_JTFUp'  )
        createinputs(fname,samplesets['JTFDown'],observables,bins,filter=varprocs['JTFDown'],htag='_JTFDown')
      
      
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
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau','mumu'], default=['mutau'], action='store',
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
  
