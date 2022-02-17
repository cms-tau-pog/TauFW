#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py -c mutau -y UL2017
import sys
from collections import OrderedDict
sys.path.append("../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = False
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt' # $PROCESS_$ANALYSIS
  tag       = "13TeV_mtlt50"
  
  for era in eras:
    for channel in channels:
      
      
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations
      
      # GET SAMPLESET
      join      = ['VV','TT','ST']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
#      sampleset = getsampleset(channel,era,fname=sname,join=join,split=None,table=False)
      sampleset = getsampleset(channel,era,fname=sname,join=join,split=[],table=False)
      
      if channel=='mumu':
        
        # RENAME (HTT convention)
        sampleset.rename('DY_M50','ZLL')
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        nomprocs = ['ZLL','W','VV','ST','TT','QCD','data_obs']
        sampleset.printtable(merged=True,split=True)
        if verbosity>=2:
          sampleset.printobjs(file=True)
      
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

        
        # TES variations for fit inputs
        varprocs = OrderedDict([ 
          ('Nom',      ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']),
          ('TES0.970', ['ZTT']),
          ('TES0.972', ['ZTT']),
          ('TES0.974', ['ZTT']),
          ('TES0.976', ['ZTT']),
          ('TES0.978', ['ZTT']),
          ('TES0.980', ['ZTT']),
          ('TES0.982', ['ZTT']),
          ('TES0.984', ['ZTT']),
          ('TES0.986', ['ZTT']),
          ('TES0.988', ['ZTT']),
          ('TES0.990', ['ZTT']),
          ('TES0.992', ['ZTT']),
          ('TES0.994', ['ZTT']),
          ('TES0.996', ['ZTT']),
          ('TES0.998', ['ZTT']),
          ('TES1.000', ['ZTT']),
          ('TES1.002', ['ZTT']),
          ('TES1.004', ['ZTT']),
          ('TES1.006', ['ZTT']),
          ('TES1.008', ['ZTT']),
          ('TES1.010', ['ZTT']),
          ('TES1.012', ['ZTT']),
          ('TES1.014', ['ZTT']),
          ('TES1.016', ['ZTT']),
          ('TES1.018', ['ZTT']),
          ('TES1.020', ['ZTT']),
          ('TES1.022', ['ZTT']),
          ('TES1.024', ['ZTT']),
          ('TES1.026', ['ZTT']),
          ('TES1.028', ['ZTT']),
          ('TES1.030', ['ZTT']),
        ])

        # Systematic uncertainties entring as NPs in fit
        sysprocs = OrderedDict([ # key, [processes], "output-name", "title/definition", [old-weight, new-weight]
          ('LTFUp',              [['ZL', 'TTL'],      "_shape_mTauFake_$BINUp",  " +2% LTF shape", ["",""]]),
          ('LTFDown',            [['ZL', 'TTL'],      "_shape_mTauFake_$BINDown"," -2% LTF shape", ["",""]]),
          ('JTFUp',              [['ZJ', 'TTJ', 'W'], "_shape_jTauFake_$BINUp",  " +5% JTF", ["",""]]),
          ('JTFDown',            [['ZJ', 'TTJ', 'W'], "_shape_jTauFake_$BINDown"," -5% JTF", ["",""]]),
          ('shape_tidUp',        [['ZTT', 'TTT'],     "_shape_tidUp",            " TID shape syst UP", ["idweight_2","idweightUp_2"]]),
          ('shape_tidDown',      [['ZTT', 'TTT'],     "_shape_tidDown",          " TID shape syst DOWN", ["idweight_2","idweightDown_2"]]),
          ('shape_mTauFakeUp',   [['ZL', 'TTL'],      "_shape_mTauFakeSFUp",     " LTF rate syst UP", ["ltfweight_2","ltfweightUp_2"]]),
          ('shape_mTauFakeDown', [['ZL', 'TTL'],      "_shape_mTauFakeSFDown",   " LTF rate syst DOWN", ["ltfweight_2","ltfweightDown_2"]]),
          ('shape_dyUp',         [['ZTT', 'ZL', 'ZJ'],"_shape_dyUp",             " +10% Zptweight", ["zptweight","(zptweight+0.1*(zptweight-1))"]]),
          ('shape_dyDown',       [['ZTT', 'ZL', 'ZJ'],"_shape_dyDown",           " -10% Zptweight", ["zptweight","(zptweight-0.1*(zptweight-1))"]]),
        ])


     
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
        
        #mvis = Var('m_vis', 10, 36, 106)
        observables = [
          Var('m_vis',              8,   50,  106, tag='',       cut="50<m_vis && m_vis<106" ),
          Var('m_2',   "m_tau_h",  13,  0.3,  1.6, tag='',       cut="0.3<m_2 && m_2<1.6", ccut=restriction, veto="dm_2==0"),
          #Var('m_2',     36, 0.23, 2.03, tag='_0p05',  cut="0.3<m_2 && m_2<2.0", ccut=restriction, veto="dm_2==0"),
          #Var('m_vis',  8, 50, 106),
		  #Var('m_2',   "m_tau_h",     26,  0.3, 1.6),
          #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
        ]
        
        # PT & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each pt/DM bin will be a separate file
        #dmbins = [0,1,10,11]
        #ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        #print ">>> DM cuts:"
        #for dm in dmbins:
        #  dmcut = "dm_2==%d"%(dm)
        #  fname = "$VAR_dm%s"%(dm)
        #  mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
        #  m2_cut   = m2.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
        #  print ">>>   %r (%r)"%(dmcut,fname)
        #  observables.append(mvis_cut)
        #  observables.append(m2_cut)
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
          Sel('DM0',      signal_regionDM0),
          Sel('DM1',      signal_regionDM1),
          Sel('DM10',     signal_regionDM10),
          Sel('DM11',     signal_regionDM11),
        ]
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      fname   = "%s/%s_%s_tes_$OBS.inputs-%s-%s.root"%(outdir,analysis,chshort,era,tag)
      if channel in ['mutau']:

        # Varied inputs
        for var in varprocs.keys():
          print "Variation: %s"%var

          if var == "Nom":
            newsampleset = sampleset
          else:
            newsampleset = sampleset.shift(varprocs[var], "_"+var.replace(".","p"), "_"+var, " %.1d"%((1.-float(var.replace("TES","")))*100.)+"% TES", split=True,filter=False,share=True)

          createinputs(fname,newsampleset, observables, bins, filter=varprocs[var], dots=True)
          newsampleset.close()

          for sys in sysprocs.keys():
            print "Systematic: %s"%sys

            if var == "Nom":
              newsampleset_sys = sampleset.shift(sysprocs[sys][0], ("_"+sys if sysprocs[sys][3][0]=="" else ""), sysprocs[sys][1], sysprocs[sys][2], split=True,filter=False,share=True)
            elif list(set(varprocs[var]) & set(sysprocs[sys][0])): # only relevant if TES variations and systematic computed for same process
              newsampleset_sys = sampleset.shift(list(set(varprocs[var]) & set(sysprocs[sys][0])), "_"+var.replace(".","p")+("_"+sys if sysprocs[sys][3][0]=="" else ""), "_"+var+sysprocs[sys][1], " %.1d"%((1.-float(var.replace("TES","")))*100.)+"% TES, "+sysprocs[sys][2], split=True,filter=False,share=True)
            else:
              continue

            createinputs(fname,newsampleset_sys, observables, bins, filter=list(set(varprocs[var]) & set(sysprocs[sys][0])), replaceweight=sysprocs[sys][3], dots=True)
            newsampleset_sys.close()



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
  
