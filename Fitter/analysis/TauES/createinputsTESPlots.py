#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards  # configures for producing plots directly
#   ./createinputs.py -c mutau -y UL2017
import sys
from collections import OrderedDict
sys.path.append("../../../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = True
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt' # $PROCESS_$ANALYSIS
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
          ('Nom',      ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          #('TESDown', ['ZTT']),
          #('TESUp', ['ZTT']),
          #('LTFUp',   ['ZL', 'TTL']),
          #('LTFDown', ['ZL', 'TTL']),
          #('JTFUp',   ['ZJ', 'TTJ', 'W']),
          #('JTFDown', ['ZJ', 'TTJ', 'W']),
          #('shape_tidUp',     ['ZTT', 'TTT']),
          #('shape_tidDown',     ['ZTT', 'TTT']),
          #('shape_mTauFakeUp',     ['ZL', 'TTL']),
          #('shape_mTauFakeDown',     ['ZL', 'TTL']),
          #('shape_dyUp',     ['ZTT', 'ZL', 'ZJ']),
          #('shape_dyDown',     ['ZTT', 'ZL', 'ZJ']),
        ])
        samplesets = { # sets of samples per variation
          'Nom':     sampleset, # nominal
          #'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p970","_TESDown"," -3.0% TES", split=True,filter=False,share=True),
          #'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p030","_TESUp",  " +3.0% TES", split=True,filter=False,share=True),
          ##'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p990","_TESDown"," -1.0% TES", split=True,filter=False,share=True),
          ##'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p010","_TESUp",  " +1.0% TES", split=True,filter=False,share=True),
          #'LTFUp':   sampleset.shift(varprocs['LTFUp'],  "_LTFUp","_LTFUp",  " +2% LTF", split=True,filter=False,share=True),
          #'LTFDown': sampleset.shift(varprocs['LTFDown'],"_LTFDown","_LTFDown"," -2% LTF", split=True,filter=False,share=True),
          #'JTFUp':   sampleset.shift(varprocs['JTFUp'],  "_JTFUp","_JTFUp",  " +5% JTF",split=True,filter=False,share=True),
          #'JTFDown': sampleset.shift(varprocs['JTFDown'],"_JTFDown","_JTFDown"," -5% JTF",split=True,filter=False,share=True),
          ##'LTFUp':   sampleset.shift(varprocs['LTFUp'],  "_LTFUp","_shape_mTauFakeSFUp",  " +2% LTF", split=True,filter=False,share=True),
          ##'LTFDown': sampleset.shift(varprocs['LTFDown'],"_LTFDown","_shape_mTauFakeSFDown"," -2% LTF", split=True,filter=False,share=True),
          ##'JTFUp':   sampleset.shift(varprocs['JTFUp'],  "_JTFUp","_shape_jTauFake_$BINUp",  " +5% JTF",split=True,filter=False,share=True),
          ##'JTFDown': sampleset.shift(varprocs['JTFDown'],"_JTFDown","_shape_jTauFake_$BINDown"," -5% JTF",split=True,filter=False,share=True),
          #'shape_tidUp':       sampleset.shift(varprocs['shape_tidUp'],"","_shape_tidUp",  " TID shape syst UP", split=True,filter=False,share=True),
          #'shape_tidDown':     sampleset.shift(varprocs['shape_tidDown'],"","_shape_tidDown",  " TID shape syst DOWN", split=True,filter=False,share=True),
          #'shape_mTauFakeUp':  sampleset.shift(varprocs['shape_mTauFakeUp'],"","_shape_mTauFakeUp",  " LTF shape syst UP", split=True,filter=False,share=True),
          #'shape_mTauFakeDown':sampleset.shift(varprocs['shape_mTauFakeDown'],"","_shape_mTauFakeDown",  " LTF shape syst DOWN", split=True,filter=False,share=True),
          #'shape_dyUp':        sampleset.shift(varprocs['shape_dyUp'],"","_shape_dyUp",  " +10% Zptweight", split=True,filter=False,share=True),
          #'shape_dyDown':      sampleset.shift(varprocs['shape_dyDown'],"","_shape_dyDown",  " -10% Zptweight", split=True,filter=False,share=True),
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
      
      restriction = {
        'dm_2==1(?!0)(?!1)': '0.35<m_2 && m_2<1.20', # [ 0.3, 1.3*sqrt(pt/100) ]
        'dm_2==10':          '0.83<m_2 && m_2<1.43', # [ 0.8, 1.5 ] -> +-3%: [ 0.824, 1.455 ], +-2%: [ 0.816, 1.470 ]
        'dm_2==11':          '0.93<m_2 && m_2<1.53', # [ 0.9, 1.6 ] -> +-3%: [ 0.927, 1.552 ], +-2%: [ 0.918, 1.568 ]
      }

      if channel=='mumu':
      
        observables = [
          Var('m_vis', 1, 60, 120, ymargin=1.6, rrange=0.08),
        ]
      
      else:
        
        mvis = Var('m_vis', 40, 0, 200)
        m2   = Var('m_2',   "m_tau_h",     26,  0.3, 1.6)
        #mvis = Var('m_vis', 10, 36, 106)
        observables = [
          Var('m_vis',    8,   50,  106, tag='',       cut="50<m_vis && m_vis<106" ),
          Var('m_2',     26, 0.23, 1.53, tag='',       cut="0.3<m_2 && m_2<2.0", ccut=restriction, veto="dm_2==0"),
          #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
        ]
        
        # PT & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each pt/DM bin will be a separate file
        dmbins = [0,1,10,11]
        #ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        print ">>> DM cuts:"
        for dm in dmbins:
          dmcut = "dm_2==%d"%(dm)
          fname = "$VAR_dm%s"%(dm)
          mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
          m2_cut   = m2.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
          print ">>>   %r (%r)"%(dmcut,fname)
          observables.append(mvis_cut)
          observables.append(m2_cut)
        #print ">>> pt cuts:"
        #for imax, ptmin in enumerate(ptbins,1):
        #  if imax<len(ptbins):
        #    ptmax = ptbins[imax]
        #    ptcut = "pt_2>%s && pt_2<=%s"%(ptmin,ptmax)
        #    fname = "$VAR_pt%sto%s"%(ptmin,ptmax)
        #  else: # overflow
        #    #ptcut = "pt_2>%s"%(ptmin)
        #    #fname = "$VAR_ptgt%s"%(ptmin)
        #    continue # skip overflow bin
        #  mvis_cut = mvis.clone(fname=fname,cut=ptcut) # create observable with extra cut for pt bin
        #  print ">>>   %r (%r)"%(ptcut,fname)
        #  observables.append(mvis_cut)
      
      
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
        
        baseline  = "(q_1*q_2<0) && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=32 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
        signal_region = "%s && mt_1<50"%(baseline)
        signal_regionDM0 = "%s && dm_2==0"%(signal_region)
        signal_regionDM1 = "%s && dm_2==1"%(signal_region)
        signal_regionDM10 = "%s && dm_2==10"%(signal_region)
        signal_regionDM11 = "%s && dm_2==11"%(signal_region)
        bins = [
          #Sel('baseline',          baseline),
          Sel('signal_region',     signal_region),
          #Sel('DM0',      signal_regionDM0),
          #Sel('DM1',      signal_regionDM1),
          #Sel('DM10',     signal_regionDM10),
          #Sel('DM11',     signal_regionDM11),
        ]
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      #fname   = "%s/%s_%s_tes_$OBS.inputs-%s-%s.root"%(outdir,analysis,chshort,era,tag)
      if channel in ['mutau']:
        createinputs(fname,samplesets['Nom'],    observables,bins,recreate=True)
        #createinputs(fname,samplesets['TESDown'],  observables,bins,filter=varprocs['TESDown'])
        #createinputs(fname,samplesets['TESUp'],  observables,bins,filter=varprocs['TESUp']  )
        #createinputs(fname,samplesets['LTFUp'],  observables,bins,filter=varprocs['LTFUp']  )
        #createinputs(fname,samplesets['LTFDown'],observables,bins,filter=varprocs['LTFDown'])
        #createinputs(fname,samplesets['JTFUp'],  observables,bins,filter=varprocs['JTFUp']) #,  htag='_JTFUp'  )
        #createinputs(fname,samplesets['JTFDown'],observables,bins,filter=varprocs['JTFDown']) #,htag='_JTFDown')
        #createinputs(fname,samplesets['shape_tidUp'],        observables,bins,htag="shape_tidUp",       filter=varprocs['shape_tidUp'],replaceweight=["idweight_2","idweightUp_2"]  )
        #createinputs(fname,samplesets['shape_tidDown'],      observables,bins,htag="shape_tidDown",     filter=varprocs['shape_tidDown'],replaceweight=["idweight_2","idweightDown_2"]  )
        #createinputs(fname,samplesets['shape_mTauFakeUp'],   observables,bins,htag="shape_mTauFakeUp",  filter=varprocs['shape_mTauFakeUp'],replaceweight=["ltfweight_2","ltfweightUp_2"]  )
        #createinputs(fname,samplesets['shape_mTauFakeDown'], observables,bins,htag="shape_mTauFakeDown",filter=varprocs['shape_mTauFakeDown'],replaceweight=["ltfweight_2","ltfweightDown_2"]  )
        #createinputs(fname,samplesets['shape_dyUp'],         observables,bins,htag="shape_dyUp",        filter=varprocs['shape_dyUp'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"]  )
        #createinputs(fname,samplesets['shape_dyDown'],       observables,bins,htag="shape_dyDown",      filter=varprocs['shape_dyDown'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"]  )
      
      
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
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], default=['UL2017'], action='store',
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
  
