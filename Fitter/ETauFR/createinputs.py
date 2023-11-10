#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020) edited by Andrea Cardini and Paola Mastrapasqua
# Description: Create input histograms for datacards
#   ./createinputs.py -c mutau -y UL2017
import sys
from collections import OrderedDict
sys.path.append("../../Plotter/") # for config.samples
from config.samples_v10 import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs, preparesysts


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  analysis  = 'zee_fr' # $PROCESS_$ANALYSIS
  tag       = args.tag
  fileexp   = "$OUTDIR/$ANALYSIS_$OBS_$CHANNEL-$ERA$TAG.inputs.root"
  outdir    = ensuredir("input")
  plotdir   = "input/plots/$ERA"
  
  for era in eras:
    for channel in channels:
      if channel=='mutau' :
        analysis  = 'zmm_fr'
      
      
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations
      
      # GET SAMPLESET
      join      = ['VV','TT','ST']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset = getsampleset(channel,era,fname=sname,join=join,split=[],table=False,tag=tag)
      
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
        systs = preparesysts( # processes to be varied
          ('Nom', "",     ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          ('TES',"_shape_tes",   ['ZTT']),
          ('FES',"_shape_fes",   ['ZL']),
          #Add other samples when EES rerun for all
          ('EES',"_shape_ees",   ['ZL','ZTT','ZJ','W','VV','ST','TTT','TTL','TTJ']), #Electron energy scale
          #('RES',"_shape_res",   ['ZL','ZTT','ZJ','W','VV','ST','TTT','TTL','TTJ']),
          #('JTFUp',   ['ZJ', 'TTJ', 'QCD', 'W']),
          #('JTFDown', ['ZJ', 'TTJ', 'QCD', 'W']),
          ERA=era,CHANNEL=channel)
        samplesets = { # sets of samples per variation
          'Nom':     sampleset, # nominal
          'TESUp':   sampleset.shift(systs['TES'].procs,"_TES1p05",systs['TES'].up," +5% TES", split=True,filter=False,share=True),
          'TESDown': sampleset.shift(systs['TES'].procs,"_TES0p95",systs['TES'].dn," -5% TES", split=True,filter=False,share=True),
          'FESUp':   sampleset.shift(systs['FES'].procs,"_FES1p10",systs['FES'].up," +10% FES", split=True,filter=False,share=True),
          'FESDown': sampleset.shift(systs['FES'].procs,"_FES0p90",systs['FES'].dn," -10% FES", split=True,filter=False,share=True),
          'EESUp':   sampleset.shift(systs['EES'].procs,"_EES1p01",systs['EES'].up," +1% EES", split=True,filter=False,share=True),
          'EESDown': sampleset.shift(systs['EES'].procs,"_EES0p99",systs['EES'].dn," -1% EES", split=True,filter=False,share=True),
          #'RESUp':   sampleset.shift(systs['RES'].procs,"",systs['RES'].up," +3% mvisRES", split=True,filter=False,share=True),
          #'RESDown': sampleset.shift(systs['RES'].procs,"",systs['RES'].dn," -3% mvisRES", split=True,filter=False,share=True),
        }
        keys = samplesets.keys() if verbosity>=1 else ['Nom','TESUp','TESDown','FESUp','FESDown','EESUp','EESDown']#,'RESUp','RESDown']
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
        
        mvis_pass = Var('m_vis', 11, 60, 120)
        mvis_fail = Var('m_vis', 1, 60, 120)
        #mvis_pass_resUp = Var('m_vis_resoUp', 11, 60, 120)
        #mvis_fail_resUp = Var('m_vis_resoUp', 1, 60, 120)
        #mvis_pass_resDown = Var('m_vis_resoDown', 11, 60, 120)
        #mvis_fail_resDown = Var('m_vis_resoDown', 1, 60, 120)
        observables_pass = []
        observables_fail = []
        #observables_pass_resUp =[]
        #observables_fail_resUp =[]
        #observables_pass_resDown =[]
        #observables_fail_resDown =[]
        
        # ADDED Eta for E->Tau FR
        # PT & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each pt/DM bin will be a separate file
        dmbins = [0,1,10,11]
        etabins = [0,1.460,1.560,2.5] #ETauFR binning
        if channel=='mutau' :
          etabins = [0,0.4,0.8,1.2,1.7,2.3] #MuTauFR binning
          
        ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        if "fr" not in analysis :
          print(">>> DM cuts:")
          for dm in dmbins:
            dmcut = "pt_2>40 && dm_2==%d"%(dm)
            fname = "$VAR_dm%s"%(dm)
            mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
            print(">>>   %r (%r)"%(dmcut,fname))
            observables.append(mvis_cut)
          print(">>> pt cuts:")
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
            print(">>>   %r (%r)"%(ptcut,fname))
            observables.append(mvis_cut)
        else :
          print(">>> eta cuts:")
          for imax,etamin in enumerate(etabins,1):
            if imax==2 or imax>=len(etabins):
              continue
            else:
              etamax = etabins[imax]
              etacut = "abs(eta_2)>%s && abs(eta_2)<=%s"%(etamin,etamax)
              fname = "$VAR_eta%sto%s"%(etamin,etamax)
            mvis_pass_cut = mvis_pass.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
            mvis_fail_cut = mvis_fail.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
            #mvis_pass_resUp_cut = mvis_pass_resUp.clone(fname=fname,cut=etacut) 
            #mvis_fail_resUp_cut = mvis_fail_resUp.clone(fname=fname,cut=etacut) 
            #mvis_pass_resDown_cut = mvis_pass_resDown.clone(fname=fname,cut=etacut) 
            #mvis_fail_resDown_cut = mvis_fail_resDown.clone(fname=fname,cut=etacut) 
            print(">>>   %r (%r)"%(etacut,fname))
            observables_pass.append(mvis_pass_cut)
            observables_fail.append(mvis_fail_cut)
            #observables_pass_resUp.append(mvis_pass_resUp_cut)
            #observables_fail_resUp.append(mvis_fail_resUp_cut)
            #observables_pass_resDown.append(mvis_pass_resDown_cut)
            #observables_fail_resDown.append(mvis_fail_resDown_cut)
          
      
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
        tauwps_sel= ['VVLoose', 'Tight']
        if channel=='mutau' :
          tauwps    = ['VLoose','Loose','Medium','Tight']
        tauwpbits = { wp: i+1 for i, wp in enumerate(tauwps)}
        iso_1     = "iso_1<0.10"
        iso_2     = "idDeepTau2018v2p5VSjet_2>=5 && idDeepTau2018v2p5VSe_2>=$WP && idDeepTau2018v2p5VSmu_2>=4"
        iso_2_fail     = "idDeepTau2018v2p5VSjet_2>=5 && idDeepTau2018v2p5VSe_2<$WP && idDeepTau2018v2p5VSmu_2>=4"
        if channel=='mutau' :
          iso_2     = "idDecayModeNewDMs_2 && idDeepTau2018v2p5VSjet_2>=5 && idDeepTau2018v2p5VSe_2>=2 && idDeepTau2018v2p5VSmu_2>=$WP"
          iso_2_fail     = "idDecayModeNewDMs_2 && idDeepTau2018v2p5VSjet_2>=5 && idDeepTau2018v2p5VSe_2>=2 && idDeepTau2018v2p5VSmu_2>=$WP"
          
        passregion  = "q_1*q_2<0 && mt_1<60 && %s && %s && !lepton_vetoes_notau && metfilter"%(iso_1,iso_2)
        failregion = "q_1*q_2<0 && mt_1<60 && %s && %s && !lepton_vetoes_notau && metfilter"%(iso_1,iso_2_fail)
        #zttregion = "%s && mt_1<60 && dzeta>-25 && abs(deta_ll)<1.5"%(baseline)
        bins_pass = [
          #Sel('baseline', repkey(baseline,WP=16)),
          #Sel('zttregion',repkey(zttregion,WP=16)),
        ]
        bins_fail = []
        TPRegion = ['_pass','_fail']
        for wpname in tauwps_sel: # loop over tauVsEle WPs
          wpbit = tauwpbits[wpname]
          for regionname in TPRegion:
            if regionname =='_pass':
                bins_pass.append(Sel(wpname+regionname,repkey(passregion,WP=wpbit)))
            else:
                bins_fail.append(Sel(wpname+regionname,repkey(failregion,WP=wpbit)))
      
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards

      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = repkey(fileexp,OUTDIR=outdir,ANALYSIS=analysis,CHANNEL=chshort,ERA=era,TAG=tag)
      createinputs(fname,samplesets['Nom'],observables_pass,bins_pass,recreate=True)
      createinputs(fname,samplesets['Nom'],observables_fail,bins_fail,recreate=False)
      if channel in ['etau']:
        createinputs(fname,samplesets['TESUp'],  observables_pass,bins_pass,systs['TES'].up,filter=systs['TES'].procs)
        createinputs(fname,samplesets['TESDown'],observables_pass,bins_pass,systs['TES'].dn,filter=systs['TES'].procs)
        createinputs(fname,samplesets['FESUp'],  observables_pass,bins_pass,systs['FES'].up,filter=systs['FES'].procs)
        createinputs(fname,samplesets['FESDown'],observables_pass,bins_pass,systs['FES'].dn,filter=systs['FES'].procs)
        createinputs(fname,samplesets['EESUp'],  observables_pass,bins_pass,systs['EES'].up,filter=systs['EES'].procs)
        createinputs(fname,samplesets['EESDown'],observables_pass,bins_pass,systs['EES'].dn,filter=systs['EES'].procs)
        #createinputs(fname,samplesets['Nom'],observables_pass,bins_pass,"_shape_resUp",shift="_resoUp")
        #createinputs(fname,samplesets['Nom'],observables_pass,bins_pass,"_shape_resDown",shift="_resoDown")
        #createinputs(fname,samplesets['RESUp'],observables_pass_resUp,bins_pass,systs['RES'].up,filter=systs['RES'].procs)
        #createinputs(fname,samplesets['RESDown'],observables_pass_resDown,bins_pass,systs['RES'].dn,filter=systs['RES'].procs)
        createinputs(fname,samplesets['TESUp'],  observables_fail,bins_fail,systs['TES'].up,filter=systs['TES'].procs)
        createinputs(fname,samplesets['TESDown'],observables_fail,bins_fail,systs['TES'].dn,filter=systs['TES'].procs)
        createinputs(fname,samplesets['FESUp'],  observables_fail,bins_fail,systs['FES'].up,filter=systs['FES'].procs)
        createinputs(fname,samplesets['FESDown'],observables_fail,bins_fail,systs['FES'].dn,filter=systs['FES'].procs)
        createinputs(fname,samplesets['EESUp'],  observables_fail,bins_fail,systs['EES'].up,filter=systs['EES'].procs)
        createinputs(fname,samplesets['EESDown'],observables_fail,bins_fail,systs['EES'].dn,filter=systs['EES'].procs)
        #createinputs(fname,samplesets['Nom'],observables_fail,bins_fail,"_shape_resUp",shift="_resoUp")
        #createinputs(fname,samplesets['Nom'],observables_fail,bins_fail,"_shape_resDown",shift="_resoDown")
        #createinputs(fname,samplesets['RESUp'],observables_fail_resUp,bins_fail,systs['RES'].up,filter=systs['RES'].procs)
        #createinputs(fname,samplesets['RESDown'],observables_fail_resDown,bins_fail,systs['RES'].dn,filter=systs['RES'].procs)
      
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        plotdir_ = ensuredir(repkey(plotdir,ERA=era,CHANNEL=channel))
        pname    = repkey(fileexp,OUTDIR=plotdir_,ANALYSIS=analysis,CHANNEL=chshort+"-$BIN",ERA=era,TAG='$TAG'+tag).replace('.root','.png')
        text     = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups   = [ ] #(['^TT','ST'],'Top'),]
        plotinputs(fname,systs,observables_pass,bins_pass,text=text,
                   pname=pname,tag=tag,group=groups)
        plotinputs(fname,systs,observables_fail,bins_fail,text=text,
                   pname=pname,tag=tag,group=groups)
      

if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2017', 'UL2018'], default=['UL2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau','mumu','etau'], default=['etau'], action='store',
                                         help="set channel" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  parser.add_argument('-t', '--tag', dest='tag', default='', action='store', help="set channel" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
