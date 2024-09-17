#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py  -y UL2017 -c <config>
import sys
from collections import OrderedDict
sys.path.append("../Plotter/") # for config.samples
# from config.samples import *
from config.samples_v12 import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs
from TauFW.Fitter.plot.rebinning import rebinning
import yaml

#nano doc: https://cms-nanoaod-integration.web.cern.ch/autoDoc/NanoAODv12/2022/2023/doc_DYJetsToLL_M-50_TuneCP5_13p6TeV-madgraphMLM-pythia8_Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2.html

map_wp_to_int = OrderedDict([('againstjet', 
				OrderedDict([('Loose',  4),
					     ('Medium', 5),
					     ('Tight',  6),
					     ('VTight', 7)])),
	                    ('againstelectron',
				OrderedDict([('VVLoose', 2),
                                             ('Tight', 6),
                                             ('Loose', 4 )]))
                           ])

def main(args):
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  againstjet = args.againstjet
  againstelectron = args.againstelectron
  setupConfFile = args.config
  DM = args.DM
  inclusive = args.inclusive
  plot      = True
  outdir    = ensuredir(f"input_pt_less_region/againstjet_{againstjet}/againstelectron_{againstelectron}")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt'

  print("Using configuration file: %s"%setupConfFile  )
  with open(setupConfFile, 'r') as file:
    setup = yaml.safe_load(file)
    if DM and 'regions' in setup or inclusive:
       newreg = {}
       for reg in setup['regions']:
          if not inclusive:
             if DM+'_' not in reg: continue
             assert(reg not in newreg)
             newreg[reg] = setup['regions'][reg]
          else:
             if 'pt' in reg: continue
             assert(reg not in newreg)
             newreg[reg] = setup['regions'][reg] 
       setup['regions'] = newreg
  channel  = setup["channel"]
  tag      = "13TeV"
  if "tag" in setup:
    tag += setup["tag"]

  for era in eras:
      
    ###############
    #   SAMPLES   #
    ###############
      
    # GET SAMPLESET
    sname     = setup["samples"]["filename"]
    sampleset = getsampleset(channel,era,fname=sname,join=setup["samples"]["join"],split=[],table=False,rmsf=setup["samples"].get("removeSFs",[]),addsf=setup["samples"].get("addSFs",[]))

    # Potentially split up samples in several processes
    if "split" in setup["samples"]:
      for splitSample in setup["samples"]["split"]:
        print("Splitting sample %s into %s"%(splitSample,setup["samples"]["split"][splitSample]))
        sampleset.split(splitSample, setup["samples"]["split"][splitSample])

    # Rename processes according to custom convention
    if "rename" in setup["samples"]:
      for renamedSample in setup["samples"]["rename"]:
        print("Renaming sample %s into %s"%(renamedSample,setup["samples"]["rename"][renamedSample]))
        sampleset.rename(renamedSample,setup["samples"]["rename"][renamedSample])

    # On-the-fly reweighting of specific processes -- do after splitting and renaming!
    if "scaleFactors" in setup:
      for SF in setup["scaleFactors"]:
        SFset = setup["scaleFactors"][SF]
        if not era in SFset["values"]: continue
        print("Reweighting with SF -- %s -- for the following processes: %s"%(SF, SFset["processes"]))
        for proc in SFset["processes"]:
          weight = "( q_1*q_2<0 ? ( "
          for cond in SFset["values"][era]:
            weight += cond+" ? "+str(SFset["values"][era][cond])+" : ("
          weight += "1.0)"
          for i in range(len(SFset["values"][era])-1):
            weight += " )"
          weight +=  ") : 1.0 )"
          print("Applying weight: %s"%weight)
          sampleset.get(proc, unique=True).addextraweight(weight)

    # Name of observed data 
    sampleset.datasample.name = setup["samples"]["data"]

     
    ###################
    #   OBSERVABLES   #
    ###################
      
    observables = []
    for obsName in setup["observables"]:
      obs = setup["observables"][obsName]
      observables.append( Var(obsName, obs["binning"][0], obs["binning"][1], obs["binning"][2], **obs["extra"]) )


    ############
    #   BINS / FIT REGIONS  #
    ############
      
    bins = [ ]
    if DM == '':
      bins.append(Sel("baseline", setup["baselineCuts"]))
    jetcut = map_wp_to_int["againstjet"][againstjet]
    electroncut = map_wp_to_int["againstelectron"][againstelectron]
    setup["baselineCuts"] = setup["baselineCuts"].replace('idDeepTau2018v2p5VSjet_2>=5', f'idDeepTau2018v2p5VSjet_2>={jetcut}')
    setup["baselineCuts"] = setup["baselineCuts"].replace('idDeepTau2018v2p5VSe_2>=2',   f'idDeepTau2018v2p5VSe_2>={electroncut}')
    print('baselinecuts: ', jetcut, '\t', againstjet, '\t', electroncut, '\t', againstelectron, '\t', setup["baselineCuts"])
    if "regions" in setup:
      for region in setup["regions"]:
        bins.append(Sel(region, setup["regions"][region]['title'], setup["baselineCuts"]+" && "+setup["regions"][region]["definition"]))


    #######################
    #   DATACARD INPUTS   #
    #######################
    # histogram inputs for the datacards
      
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
    chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel

    fname   = "%s/%s_%s_tes_$OBS%s.inputs-%s-%s.root"%(outdir,analysis,chshort,DM,era,tag)

    print("Nominal inputs")
    createinputs(fname, sampleset, observables, bins, filter=setup["processes"], dots=True, parallel=parallel)

    if "TESvariations" in setup:
      for var in setup["TESvariations"]["values"]:
        print("Variation: TES = %f"%var)

        newsampleset = sampleset.shift(setup["TESvariations"]["processes"], ("_TES%.3f"%var).replace(".","p"), "_TES%.3f"%var, " %.1d"%((1.-var)*100.)+"% TES", split=True,filter=False,share=True)
        createinputs(fname,newsampleset, observables, bins, filter=setup["TESvariations"]["processes"], dots=True, parallel=parallel)

    if "systematics" in setup:
      for sys in setup["systematics"]:

        sysDef = setup["systematics"][sys]
        if sysDef["effect"] != "shape":
          continue
        print("Systematic: %s"%sys)

        # Iterate through the variations of the systematic
        for iSysVar in range(len(sysDef["variations"])):

          # Extract relevant parameters for modifying the sample
          sampleAppend = sysDef["sampleAppend"][iSysVar] if "sampleAppend" in sysDef else ""
          weightReplaced = [sysDef["nomWeight"],sysDef["altWeights"][iSysVar]] if "altWeights" in sysDef else ["",""]
          # Create a new sample set with systematic variations
          newsampleset_sys = sampleset.shift(sysDef["processes"], sampleAppend, "_"+sysDef["name"]+sysDef["variations"][iSysVar], sysDef["title"], split=True,filter=False,share=True)
          createinputs(fname,newsampleset_sys, observables, bins, filter=sysDef["processes"], replaceweight=weightReplaced, dots=True, parallel=parallel)

          # Check for overlap with TES variations in setup
          if "TESvariations" in setup:
            overlap_TES_sys = list( set(sysDef["processes"]) & set(setup["TESvariations"]["processes"]) )
            # If overlap exists, apply TES variations
            if overlap_TES_sys:
              for var in setup["TESvariations"]["values"]:
                print("Variation: TES = %f"%var)
                newsampleset_TESsys = sampleset.shift(overlap_TES_sys, ("_TES%.3f"%var).replace(".","p")+sampleAppend, "_TES%.3f"%var+"_"+sysDef["name"]+sysDef["variations"][iSysVar], " %.1d"%((1.-var)*100.)+"% TES" + sysDef["title"], split=True,filter=False,share=True)
                createinputs(fname,newsampleset_TESsys, observables, bins, filter=overlap_TES_sys, replaceweight=weightReplaced, dots=True, parallel=parallel)

      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
        text   = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups = [ ] #(['^TT','ST'],'Top'),]

        if "mumu" in channel:
            varprocs = OrderedDict([
                       ('Nom',      ['ZL','ZTT', 'ZJ','W','ST','TT','QCD','data_obs'])])
        elif "mutau"in channel:
            varprocs = OrderedDict([
                       ('Nom',      ["ZTT","ZL","ZJ","W","VV","ST","TTT","TTL","TTJ","QCD","data_obs"])])

        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups, paralel=parallel)
        rebinning(fname, obs=observables[0].filename, tag=tag) 
        fname = fname.split('/')[0] + '/rebinning/' + fname.split('/')[-1]
        plotdir   = ensuredir(plotdir,"rebinning")
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups, parallel=parallel)
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s_wqcd_subtracted.png"%(plotdir,analysis,chshort,era,tag)
        varprocs = OrderedDict([
                       ('Nom',      ['ZTT', 'data_obs_nonztt_subtratced'])])
        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups, parallel=parallel, mean=True) 

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', default=['UL2017'], action='store', help="set era" )
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store',
                                         help="set config file containing sample & fit setup" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  parser.add_argument('-d', '--decaymode', dest='DM', type=str, default='', help="which decay mode" )
  parser.add_argument('-i', '--inclusive', dest='inclusive', action='store_true', default=False, help="which pt region" )
  parser.add_argument('-j', '--jet', dest='againstjet', default='Medium', help="against jet cut")
  parser.add_argument('-e', '--electron', dest='againstelectron', default='VVLoose', help="against electron cut")
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print("\n>>> Done.")
  
