#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py -c mutau -y UL2017
import sys
sys.path.append("../../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs, preparesysts


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  analysis  = 'ztt_tid' # $PROCESS_$ANALYSIS
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
      join      = ['VV','TT','ST']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
      sampleset = getsampleset(channel,era,fname=sname,join=join,split=None,table=False,
                               rmsf=['idweight_2','ltfweight_2'])
      
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
        splitbydm = True and False # split by DM for public plots
        if splitbydm:
          sampleset.split('DY',[('ZTT_DM0', GMR+" && dm_2==0"), ('ZTT_DM1', GMR+" && dm_2==1"),
                                ('ZTT_DM10',GMR+" && dm_2==10"),('ZTT_DM11',GMR+" && dm_2==11"),
                                ('ZL',GML),('ZJ',GMJ)])
          sampleset.get('DY',unique=True).replaceweight('*idweight_2','',verb=2) # remove tau ID SF
        else:
          sampleset.split('DY',[('ZTT',GMR),('ZL',GML),('ZJ',GMJ),])
        sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
        #sampleset.split('ST',[('STT',GMR),('STJ',GMF),]) # small background
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        systs = preparesysts( # prepare systematic variations: syskey, systag, procs
          ('Nom',"",          ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          ('TES',"_shape_tes",['ZTT','TTT']),           # tau energy scale
          ('LTF',"_shape_ltf",['ZL', 'TTL']),           # l -> tau energy scale
          ('JTF',"_shape_jtf",['ZJ', 'TTJ','QCD','W']), # j -> tau energy scale
          #('tid',"_shape_tid",['ZTT','TTT'],     ('idweight_2','idweightUp_2','idweightDown_2')), # replace 'idweight_2'
          ('zpt',"_shape_dy", ['ZTT','ZL','ZJ'], ('zptweight','(1.1*zptweight-0.1)','(0.9*zptweight+0.1)')), # replace 'zptweight'
          ERA=era,CHANNEL=channel) # keys to replace in systag
        if splitbydm:
          for syskey, syst in systs.iteritems():
            if 'ZTT' in syst.procs:
              syst.procs = ['ZTT_DM0','ZTT_DM1','ZTT_DM10','ZTT_DM11']+syst.procs[1:]
        samplesets = { # create new sets of samples per energy scale variation
          'Nom':     sampleset, # nominal
          'TESUp':   sampleset.shift(systs['TES'].procs,"_TES1p030",systs['TES'].up," +3% TES", split=True,filter=False,share=True),
          'TESDown': sampleset.shift(systs['TES'].procs,"_TES0p970",systs['TES'].dn," -3% TES", split=True,filter=False,share=True),
          #'TESUp':   sampleset.shift(systs['TES'].procs,"_TESUp",  systs['TES'].up," +3% TES", split=True,filter=False,share=True),
          #'TESDown': sampleset.shift(systs['TES'].procs,"_TESDown",systs['TES'].dn," -3% TES", split=True,filter=False,share=True),
          'LTFUp':   sampleset.shift(systs['LTF'].procs,"_LTF1p030",systs['LTF'].up," +3% LTF", split=True,filter=False,share=True),
          'LTFDown': sampleset.shift(systs['LTF'].procs,"_LTF0p970",systs['LTF'].dn," -3% LTF", split=True,filter=False,share=True),
          'JTFUp':   sampleset.shift(systs['JTF'].procs,"_JTF1p100",systs['JTF'].up," +10% JTF",split=True,filter=False,share=True),
          'JTFDown': sampleset.shift(systs['JTF'].procs,"_JTF0p900",systs['JTF'].dn," -10% JTF",split=True,filter=False,share=True),
        }
        keys = samplesets.keys() if verbosity>=1 else ['Nom','TESUp','TESDown']
        for shift in keys: # print table
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
          Var('m_vis', 1, 60, 120, fname='mvis', ymargin=1.6, rrange=0.08),
        ]
      
      else:
        
        mvis = Var('m_vis', 30, 50, 200, fname='mvis')
        observables = [
          #Var('dm_2==0 ? 0.13957 : m_2', "m_tau", 18, 0, 1.8, fname='mtau'),
          Var('m_vis', 30, 50, 200, fname='mvis', cbins={'pt_2>70':(15, 50, 200)}),
          #Var('m_vis', 38, 10, 200, fname='mvis'), # broad range
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
          fname = "$FILE_dm%s"%(dm)
          mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
          print ">>>   %r (%r)"%(dmcut,fname)
          observables.append(mvis_cut)
        print ">>> pt cuts:"
        for imax, ptmin in enumerate(ptbins,1):
          if imax<len(ptbins):
            ptmax = ptbins[imax]
            ptcut = "pt_2>%s && pt_2<=%s"%(ptmin,ptmax)
            fname = "$FILE_pt%sto%s"%(ptmin,ptmax)
          else: # overflow
            #ptcut = "pt_2>%s"%(ptmin)
            #fname = "$FILE_ptgt%s"%(ptmin)
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
        tauwps    = ['Tight'] # only do Tight
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
      fname   = repkey(fileexp,OUTDIR=outdir,ANALYSIS=analysis,CHANNEL=chshort,ERA=era,TAG=tag)
      createinputs(fname,samplesets['Nom'],observables,bins,recreate=True)
      if channel in ['mutau']:
        createinputs(fname,samplesets['TESUp'],  observables,bins,systs['TES'].up,filter=systs['TES'].procs)
        createinputs(fname,samplesets['TESDown'],observables,bins,systs['TES'].dn,filter=systs['TES'].procs)
        createinputs(fname,samplesets['LTFUp'],  observables,bins,systs['LTF'].up,filter=systs['LTF'].procs)
        createinputs(fname,samplesets['LTFDown'],observables,bins,systs['LTF'].dn,filter=systs['LTF'].procs)
        createinputs(fname,samplesets['JTFUp'],  observables,bins,systs['JTF'].up,filter=systs['JTF'].procs)
        createinputs(fname,samplesets['JTFDown'],observables,bins,systs['JTF'].dn,filter=systs['JTF'].procs)
        #createinputs(fname,samplesets['Nom'],observables,bins,systs['tid'].up,filter=systs['tid'].procs,replaceweight=systs['tid'].wgtup)
        #createinputs(fname,samplesets['Nom'],observables,bins,systs['tid'].dn,filter=systs['tid'].procs,replaceweight=systs['tid'].wgtdn)
        createinputs(fname,samplesets['Nom'],observables,bins,systs['zpt'].up,filter=systs['zpt'].procs,replaceweight=systs['zpt'].wgtup)
        createinputs(fname,samplesets['Nom'],observables,bins,systs['zpt'].dn,filter=systs['zpt'].procs,replaceweight=systs['zpt'].wgtdn)
      
      
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        plotdir_ = ensuredir(repkey(plotdir,ERA=era,CHANNEL=channel))
        pname    = repkey(fileexp,OUTDIR=plotdir_,ANALYSIS=analysis,CHANNEL=chshort+"-$BIN",ERA=era,TAG='$TAG'+tag).replace('.root','.png')
        text     = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups   = [ ] #(['^TT','ST'],'Top'),]
        plotinputs(fname,systs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups)
      


if __name__ == "__main__":
  from argparse import ArgumentParser
  eras = ['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018']
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=eras, default=['UL2017'], action='store',
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
  
