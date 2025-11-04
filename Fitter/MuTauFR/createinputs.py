#! /usr/bin/env python3
#Based on createinputs.py created by Izaak N.
# Stepan Zakharov  2023
# Alexei Raspereza 2024 
import sys
import os
from collections import OrderedDict
#from IPython import embed
#sys.path.append("../../Plotter/") # for config.samples
from samples_MuTauFR import *
from TauFW.Plotter.plot.utils import LOG#, STYLE, ensuredir, repkey, Var, Sel
from TauFW.Fitter.plot.datacard import createinputs, plotinputs, preparesysts #, rename_QCD
import numpy as np
from ROOT import TFile

etabins = {
  '0to0p9'   : [0.0,0.9],
  '0p9to1p2' : [0.9,1.2],
  '1p2to2p1' : [1.2,2.1],
  '2p1to2p5' : [2.1,2.5],
  '0to2p5'   : [0.0,2.5],
}

vs_e_jet_wps = {'VVVLoose'   : 1,
                'VVLoose'    : 2,
                'VLoose'     : 3,
                'Loose'      : 4,
                'Medium'     : 5,
                'Tight'      : 6,
                'VTight'     : 7,
                'VVTight'    : 8,}

vs_mu_wps = {'VLoose'   : 1,
             'Loose'    : 2,
             'Medium'   : 3,
             'Tight'    : 4}

def gen_deeptau_cut(VSe=None, invVSe=False, VSmu=None, invVSmu=False, VSjet=None, invVSjet=False):
  """
    Generate a cut line based on DeepTau variables and their associated working points.

    Args:
      VSe (str): Electron working point. Possible values: 'VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight'.
      invVSe (bool): Flag indicating if the inverse comparison should be used for VSe.
      VSmu (str): Muon working point. Possible values: 'VLoose', 'Loose', 'Medium', 'Tight' or the content of the variable if it's not from the set before. 
      invVSmu (bool): Flag indicating if the inverse comparison should be used for VSmu.
      VSjet (str): Jet working point. Possible values: 'VVVLoose', 'VVLoose', 'VLoose', 'Loose', 'Medium', 'Tight', 'VTight', 'VVTight'.
      invVSjet (bool): Flag indicating if the inverse comparison should be used for VSjet.

    Returns:
      str: A string representing the cut line based on the provided DeepTau variables and working points.
  """
  cut_line = ''

  deeptauvar = 'idDeepTau2018v2p5'
  arg_before = False
  if VSe:
    cut_line += '%sVSe_2%s%d'%(deeptauvar, "<" if invVSe else ">=", vs_e_jet_wps[VSe])
    arg_before = True
  if VSmu:
    if arg_before: cut_line += ' && '
    cut_line += '%sVSmu_2%s%s'%(deeptauvar, "<" if invVSmu else ">=", str(vs_mu_wps[VSmu]) if VSmu in vs_mu_wps else VSmu)
    arg_before = True
  if VSjet:
    if arg_before: cut_line += ' && '
    cut_line += '%sVSjet_2%s%d'%(deeptauvar, "<" if invVSjet else ">=", vs_e_jet_wps[VSjet])
  return cut_line


def main(args):
  nthreads  = args.parallel
  verbosity = args.verbosity
  plot      = False
  create_inputs = True

  wp_vs_mu  = args.wp_vs_mu
  wp_vs_jet = args.wp_vs_jet
  wp_vs_e   = args.wp_vs_e

  cmssw_dir = os.getenv('CMSSW_BASE')
  base_dir = ensuredir('%s/src/TauFW/Fitter/MuTauFR/input'%(cmssw_dir))
  inputs_dir = ensuredir('%s/%sVsJet_%sVsMu_%sVsE'%(base_dir,wp_vs_jet,wp_vs_mu,wp_vs_e))
  plot_dir   = ensuredir('%s/plots'%(inputs_dir))
  analysis  = 'MuTauFR' # $PROCESS_$ANALYSIS
  tag       = ""
  channel   = args.channel[0]
  etabin    = args.etabin
  era       = args.era[0]

#  tauwps = {key : bit for key, bit in tau_vs_mu_wps.items() if key in ['VLoose', 'Loose', 'Medium','Tight']}


  ###############
  #   SAMPLES   #
  ###############
  # sample set and their systematic variations
  
  # GET SAMPLESET
  arg_dict = vars(args)
  arg_dict['join'] =  ['VV','TT','ST'] # common weight for MC
  arg_dict['fname'] = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  arg_dict['split'] = []
  arg_dict['table'] = False
  era = arg_dict.pop('era')[0]
  channel = arg_dict.pop('channel')[0]
 
  print(arg_dict)
  sampleset = getsampleset(channel,
                           era,
                           **arg_dict)
  
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
    ''' 11.01.2024 Information from Andrea Cardini:
    genmatch_2 can have 6 values:
      0 - jet
      1 - prompt electron
      2 - prompt muon
      3 - electron from tau
      4 - muon from tau
      5 - hadronic tau
    '''
    
    # SPLIT & RENAME (HTT convention)
    GMR = "genmatch_2==5" 
    GML = "genmatch_2!=0 && genmatch_2!=5"
    GMJ = "genmatch_2==0"
    GMM = "genmatch_2==2"
    sampleset.split('DY',[('ZTT',GMR),('ZMM',GMM),('ZJ',GMJ)])
    sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
    #sampleset.split('ST',[('STT',GMR),('STJ',GMF),]) # small background
    sampleset.rename('WJ','W')
    sampleset.datasample.name = 'data_obs'
    #########################################################################
    
    #########################################################################
    
    # SYSTEMATIC VARIATIONS
    varprocs = OrderedDict([ # processes to be varied
      ('Nom',     ['ZTT','ZMM','ZJ','W','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ','VV'
      ('TESUp',   ['ZTT','TTT']),
      ('TESDown', ['ZTT','TTT']),
      ('FESUp',   ['ZMM','TTL']),
      ('FESDown', ['ZMM','TTL']),
      #      ('shape_resUp',   ['ZMM']),
      #      ('shape_resDown', ['ZMM']),
    ])
    samplesets = { # sets of samples per variation
      'Nom':     sampleset, # nominal
      'TESUp':   sampleset.shift(varprocs['TESUp'],  "_TES1p030","_TESUp",  " +3% TES", split=True,filter=False,share=True),
      'TESDown': sampleset.shift(varprocs['TESDown'],"_TES0p970","_TESDown"," -3% TES", split=True,filter=False,share=True),
      'FESUp':   sampleset.shift(varprocs['FESUp'],  "_LTF1p030","_FESUp",  " +3% FES", split=True,filter=False,share=True),
      'FESDown': sampleset.shift(varprocs['FESDown'],"_LTF0p970","_FESDown"," -3% FES", split=True,filter=False,share=True),
    }
    keys = samplesets.keys()
    for shift in keys:
      if not shift in samplesets: continue
      samplesets[shift].printtable(merged=True,split=True)
      if verbosity>=2:
        samplesets[shift].printobjs(file=True)

  ###################
  #   OBSERVABLES   #
  ###################
  # observable/variables to be fitted in combine
  low_bin = 40
  high_bin = 140 
  n_bins = 10 
  
  mvis_pass = Var('m_vis', n_bins, low_bin, high_bin)
  mvis_fail = Var('m_vis', 1, low_bin, high_bin, tag="")
  
  #  mvis_pass_resUp = Var('m_vis_resoUp', n_bins, low_bin, high_bin)
  #  mvis_fail_resUp = Var('m_vis_resoUp', 1, low_bin, high_bin, tag="")
  
  #  mvis_pass_resDown = Var('m_vis_resoDown', n_bins, low_bin, high_bin)
  #  mvis_fail_resDown = Var('m_vis_resoDown', 1, low_bin, high_bin, tag="")
  
  observables_pass = []
  observables_fail = []
  #  observables_pass_resUp =[]
  #  observables_fail_resUp =[]
  #  observables_pass_resDown =[]
  #  observables_fail_resDown =[]
        
  #  etabins = np.array([0,0.9,1.2,2.1,2.5])
  #  etabins_low = np.append(etabins[:-1], [0])
  #  etabins_high = np.append(etabins[1:], [2.5])
  
  print (">>> eta cuts:")
  lowbin = etabins[etabin][0]
  highbin = etabins[etabin][1]

  etacut = "abs(eta_2)>%s && abs(eta_2)<=%s"%(lowbin,highbin)
  fname = "$VAR_eta%sto%s"%(lowbin,highbin)
  mvis_pass_cut = mvis_pass.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
  mvis_fail_cut = mvis_fail.clone(fname=fname,cut=etacut) # create observable with extra cut for eta bin
  
  #    mvis_pass_resUp_cut = mvis_pass_resUp.clone(fname=fname,cut=etacut) 
  #    mvis_fail_resUp_cut = mvis_fail_resUp.clone(fname=fname,cut=etacut) 
  #    mvis_pass_resDown_cut = mvis_pass_resDown.clone(fname=fname,cut=etacut) 
  #    mvis_fail_resDown_cut = mvis_fail_resDown.clone(fname=fname,cut=etacut) 
    
  print (">>>   %r (%r)"%(etacut,fname))
    
  observables_pass.append(mvis_pass_cut)
  observables_fail.append(mvis_fail_cut)
  #    observables_pass_resUp.append(mvis_pass_resUp_cut)
  #    observables_fail_resUp.append(mvis_fail_resUp_cut)
  #    observables_pass_resDown.append(mvis_pass_resDown_cut)
  #    observables_fail_resDown.append(mvis_fail_resDown_cut)
  
  ############
  #   BINS   #
  ############
  # selection categories
  tau_sel = 'idDecayModeNewDMs_2 && pt_2>20 && fabs(eta_2)<2.5 && (dm_2==0 || dm_2==1)'
  mu_sel  = 'iso_1<0.15 && q_1*q_2<0 && pt_1>26 && fabs(eta_1)<2.4 && idMedium_1'
  filters = '!lepton_vetoes_notau && metfilter'
  iso_2      = gen_deeptau_cut(VSe=wp_vs_e, VSmu=wp_vs_mu, VSjet=wp_vs_jet)
  iso_2_fail = gen_deeptau_cut(VSe=wp_vs_e, VSmu=wp_vs_mu, invVSmu=True, VSjet=wp_vs_jet)
  print('')
  print('ISO_2 : %s'%(iso_2))
  print('ISO_2_FAIL : %s'%(iso_2_fail))
  baseline       = "%s && %s && %s && %s"%(filters,mu_sel,tau_sel,iso_2)
  baseline_fail  = "%s && %s && %s && %s"%(filters,mu_sel,tau_sel,iso_2_fail)
  zttregion      = "%s && mt_1<40"%(baseline)
  zttregion_fail = "%s && mt_1<40"%(baseline_fail)
  print('')
  print('Pass : %s'%(zttregion))
  print('Fail : %s'%(zttregion_fail))
  print('')
  bins_pass = []
  bins_fail = []
  TPRegion = ['pass','fail']
  wpbit = vs_mu_wps[wp_vs_mu]
  for regionname in TPRegion:
    if regionname =='pass':
      bins_pass.append(Sel(wp_vs_mu+'_'+regionname,repkey(zttregion,WP=wpbit)))
    else:
      bins_fail.append(Sel(wp_vs_mu+'_'+regionname,repkey(zttregion_fail,WP=wpbit)))

  #######################
  #   DATACARD INPUTS   #
  #######################
  # histogram inputs for the datacards
  chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
  fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(inputs_dir,analysis,chshort,era,tag)
  print('inputs file %s'%(fname))
  if create_inputs:
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
    createinputs(fname,samplesets['Nom'],     observables_pass, bins_pass, recreate=True, parallel=nthreads)
#    createinputs(fname,samplesets['Nom'],     observables_pass, bins_pass,  "_shape_resUp",   shift="_resoUp", filter=['ZMM'])
#    createinputs(fname,samplesets['Nom'],     observables_pass, bins_pass,  "_shape_resDown", shift="_resoDown", filter=['ZMM'])
    createinputs(fname,samplesets['TESUp'],   observables_pass, bins_pass, filter=varprocs['TESUp'], parallel=nthreads)
    createinputs(fname,samplesets['TESDown'], observables_pass, bins_pass, filter=varprocs['TESDown'], parallel=nthreads)
    createinputs(fname,samplesets['FESUp'],   observables_pass, bins_pass, filter=varprocs['FESUp'], parallel=nthreads)
    createinputs(fname,samplesets['FESDown'], observables_pass, bins_pass, filter=varprocs['FESDown'], parallel=nthreads)
  
    createinputs(fname,samplesets['Nom'],     observables_fail, bins_fail, recreate=False, parallel=nthreads)
#    createinputs(fname,samplesets['Nom'],     observables_fail,bins_fail,"_shape_resUp",shift="_resoUp", filter=['ZMM'])
#    createinputs(fname,samplesets['Nom'],     observables_fail,bins_fail,"_shape_resDown",shift="_resoDown",filter=['ZMM'])
    createinputs(fname,samplesets['TESUp'],   observables_fail, bins_fail, filter=varprocs['TESUp'], parallel=nthreads)
    createinputs(fname,samplesets['TESDown'], observables_fail, bins_fail, filter=varprocs['TESDown'], parallel=nthreads)
    createinputs(fname,samplesets['FESUp'],   observables_fail, bins_fail, filter=varprocs['FESUp'], parallel=nthreads)
    createinputs(fname,samplesets['FESDown'], observables_fail, bins_fail, filter=varprocs['FESDown'], parallel=nthreads)
  
#  rename_QCD(fname,observables_pass)
  
  ############
  #   PLOT   #
  ############
  # control plots of the histogram inputs
  
  if plot:
    pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plot_dir,analysis,chshort,era,tag)
    text   = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
    groups = [] #(['^TT','ST'],'Top'),]
    plotinputs(fname,varprocs,observables_pass,bins_pass,text=text,pname=pname,tag=tag,group=groups)
    plotinputs(fname,varprocs,observables_fail,bins_fail,text=text,pname=pname,tag=tag,group=groups)

if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='era', nargs='+', choices=['2016','2017','2018','UL2017','UL2018','UL2016_postVFP','UL2016_preVFP','UL2018_withJEC','2022_postEE','2022_preEE','2023C', '2023D','2024'], default='2024', action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channel', nargs='*', default='mutau', action='store',
                                         help="set channel" )
#  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
#                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-parallel', '--parallel', type=int, default=20, dest='parallel', 
                                         help="threads")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  parser.add_argument('-wp_vs_e','--wp_vs_e',dest='wp_vs_e',default='VVLoose',choices=['VVLoose','Tight'])
  parser.add_argument('-wp_vs_mu','--wp_vs_mu',dest='wp_vs_mu',default='VLoose',choices=['VLoose','Tight'])
  parser.add_argument('-wp_vs_jet','--wp_vs_jet',dest='wp_vs_jet',default='Medium',choices=['Medium','Tight'])
  parser.add_argument('-etabin','--etabin',dest='etabin',default='0to0p9',choices=['0to0p9','0p9to1p2','1p2to2p1','2p1to2p5'])
  parser.add_argument('-dry_run','--dry_run',dest='dry_run',action='store_true')
  args = parser.parse_args()
  #LOG.verbosity = args.verbosity
  #PLOG.verbosity = args.verbosity
  main(args)
  print ("\n>>> Done.")
  
