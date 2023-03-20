#! /usr/bin/env python
# Author: Yiwen Wen (August 2020)
# Based on createinputs.py created by Izaak N.
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
  analysis  = 'MuTauFR' # $PROCESS_$ANALYSIS
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
        GMM = "genmatch_2==2"
        GMTL = "genmatch_2>2 && genmatch_2<5"
        sampleset.split('DY',[('ZTT',GMR),('ZMM',GMM),('ZJ',GMJ),('ZTL',GMTL)])
        sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
        #sampleset.split('ST',[('STT',GMR),('STJ',GMF),]) # small background
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        varprocs = OrderedDict([ # processes to be varied
          ('Nom',     ['ZTT','ZMM','ZTL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          ('TESUp',   ['ZTT','TTT']),
          ('TESDown', ['ZTT','TTT']),
          ('FESUp',   ['ZMM','ZTL','TTL']),
          ('FESDown', ['ZMM','ZTL','TTL']),
          ('RESUp',   ['ZMM']),
          ('RESDown', ['ZMM']),
        ])
        samplesets = { # sets of samples per variation
          'Nom':     sampleset, # nominal
          'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p03","_TESUp",  " +3% TES", split=True,filter=False,share=True),
          'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p97","_TESDown"," -3% TES", split=True,filter=False,share=True),
          'FESUp':   sampleset.shift(varprocs['FESUp'],  "_FES1p05","_FESUp",  " +5% FES", split=True,filter=False,share=True),
          'FESDown': sampleset.shift(varprocs['FESDown'],"_FES0p95","_FESDown"," -5% FES", split=True,filter=False,share=True),
          'RESUp':   sampleset.shift(varprocs['RESUp'],  "_RES1p20","_RESUp",  " +20% RES", split=True,filter=False,share=True),
          'RESDown': sampleset.shift(varprocs['RESDown'],"_RES0p80","_RESDown"," -20% RES", split=True,filter=False,share=True),
        }
        keys = samplesets.keys() if verbosity>=1 else ['Nom','TESUp','TESDown','FESUp','FESDown','RESUp','RESDown']
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
        
        mvis_pass = Var('m_vis', 10, 70, 120)
        mvis_fail = Var('m_vis', 1, 70, 120)
        observables_pass = [
          #Var('m_vis', 10, 70, 120),
          #Var('m_vis', 1, 70, 120, tag="_Fail"),
          #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
        ]
        
        observables_fail = [
          #Var('m_vis', 1, 70, 120),
        ]
        
        # eta & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each eta/DM bin will be a separate file
        #dmbins = [0,1,10,11]
        etabins = [0,0.4,0.8,1.2,1.7,3.0]
        #ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        #print ">>> DM cuts:"
        #for dm in dmbins:
          #dmcut = "pt_2>20 && dm_2==%d"%(dm)#dmcut = "pt_2>40 && dm_2==%d"%(dm)
          #fname = "$VAR_dm%s"%(dm)
          #mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
          #print ">>>   %r (%r)"%(dmcut,fname)
          #observables.append(mvis_cut)
        print ">>> eta cuts:"
        for imax, etamin in enumerate(etabins,1):
          if imax<len(etabins):
            etamax = etabins[imax]
            etacut = "abs(eta_2)>%s && abs(eta_2)<=%s"%(etamin,etamax)
            fname = "$VAR_eta%sto%s"%(etamin,etamax)
          else: # overflow
            #ptcut = "pt_2>%s"%(ptmin)
            #fname = "$VAR_ptgt%s"%(ptmin)
            continue # skip overflow bin
          mvis_pass_cut = mvis_pass.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
          mvis_fail_cut = mvis_fail.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
          print ">>>   %r (%r)"%(etacut,fname)
          observables_pass.append(mvis_pass_cut)
          observables_fail.append(mvis_fail_cut)
      
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
        
        tauwps    = ['Medium']#,'Tight']
        tauwpbits = { wp: 2**i for i, wp in enumerate(tauwps)}
        iso_1     = "iso_1<0.15"
        iso_2     = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSmu_2>=$WP && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=4"
        iso_2_fail     = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSmu_2<$WP && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=4"
        if era=='UL2017':
            pt_1 = "pt_1>29"
        else:
            pt_1 = "pt_1>26"
        baseline  = "q_1*q_2<0 && %s && %s && %s &&!lepton_vetoes_notau && metfilter"%(iso_1,iso_2,pt_1)
        baseline_fail  = "q_1*q_2<0 && %s && %s && %s &&!lepton_vetoes_notau && metfilter"%(iso_1,iso_2_fail,pt_1)
        zttregion = "%s && mt_1<40"%(baseline)
        zttregion_fail = "%s && mt_1<40"%(baseline_fail)
        bins_pass = []
        bins_fail = []
        TPRegion = ['Pass','Fail']
        for wpname in tauwps: # loop over tau ID WPs
          wpbit = tauwpbits[wpname]
          for regionname in TPRegion:
            if regionname =='Pass':
                bins_pass.append(Sel(wpname+regionname,repkey(zttregion,WP=wpbit)))
            else:
                bins_fail.append(Sel(wpname+regionname,repkey(zttregion_fail,WP=wpbit)))
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      createinputs(fname,samplesets['Nom'],    observables_pass,bins_pass,recreate=True)
      if channel in ['mutau']:
        createinputs(fname,samplesets['TESUp'],  observables_pass,bins_pass,filter=varprocs['TESUp'])
        createinputs(fname,samplesets['TESDown'],observables_pass,bins_pass,filter=varprocs['TESDown'])
        createinputs(fname,samplesets['FESUp'],  observables_pass,bins_pass,filter=varprocs['FESUp'])
        createinputs(fname,samplesets['FESDown'],observables_pass,bins_pass,filter=varprocs['FESDown'])
        createinputs(fname,samplesets['RESUp'],  observables_pass,bins_pass,filter=varprocs['RESUp'])
        createinputs(fname,samplesets['RESDown'],observables_pass,bins_pass,filter=varprocs['RESDown'])
       
      createinputs(fname,samplesets['Nom'],    observables_fail,bins_fail,recreate=False)
      if channel in ['mutau']:
        createinputs(fname,samplesets['TESUp'],  observables_fail,bins_fail,filter=varprocs['TESUp'])
        createinputs(fname,samplesets['TESDown'],observables_fail,bins_fail,filter=varprocs['TESDown'])
        createinputs(fname,samplesets['FESUp'],  observables_fail,bins_fail,filter=varprocs['FESUp'])
        createinputs(fname,samplesets['FESDown'],observables_fail,bins_fail,filter=varprocs['FESDown'])
        createinputs(fname,samplesets['RESUp'],  observables_fail,bins_fail,filter=varprocs['RESUp'])
        createinputs(fname,samplesets['RESDown'],observables_fail,bins_fail,filter=varprocs['RESDown'])

      
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
        text   = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups = [] #(['^TT','ST'],'Top'),]
        plotinputs(fname,varprocs,observables_pass,bins_pass,text=text,pname=pname,tag=tag,group=groups)
        plotinputs(fname,varprocs,observables_fail,bins_fail,text=text,pname=pname,tag=tag,group=groups)
      
      

if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017','UL2018','UL2016_postVFP','UL2016_preVFP','UL2018_withJEC'], default=['UL2017'], action='store',
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
  
