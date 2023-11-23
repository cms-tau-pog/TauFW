#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py  -y UL2017 -c <config>
import sys
from collections import OrderedDict
sys.path.append("../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs
import yaml


def main(args):
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  setupConfFile = args.config
  plot      = True
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt'

  print "Using configuration file: %s"%setupConfFile  
  with open(setupConfFile, 'r') as file:
    setup = yaml.safe_load(file)

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
        print "Splitting sample %s into %s"%(splitSample,setup["samples"]["split"][splitSample])
        sampleset.split(splitSample, setup["samples"]["split"][splitSample])

    # Rename processes according to custom convention
    if "rename" in setup["samples"]:
      for renamedSample in setup["samples"]["rename"]:
        print "Renaming sample %s into %s"%(renamedSample,setup["samples"]["rename"][renamedSample])
        sampleset.rename(renamedSample,setup["samples"]["rename"][renamedSample])

    # On-the-fly reweighting of specific processes -- do after splitting and renaming!
    if "scaleFactors" in setup:
      for SF in setup["scaleFactors"]:
        SFset = setup["scaleFactors"][SF]
        if not era in SFset["values"]: continue
        print "Reweighting with SF -- %s -- for the following processes: %s"%(SF, SFset["processes"])
        for proc in SFset["processes"]:
          weight = "( q_1*q_2<0 ? ( "
          for cond in SFset["values"][era]:
            weight += cond+" ? "+str(SFset["values"][era][cond])+" : ("
          weight += "1.0)"
          for i in range(len(SFset["values"][era])-1):
            weight += " )"
          weight +=  ") : 1.0 )"
          print "Applying weight: %s"%weight
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
      
    bins = [ Sel("baseline", setup["baselineCuts"]) ]
    if "regions" in setup:
      for region in setup["regions"]:
        bins.append(Sel(region, setup["baselineCuts"]+" && "+setup["regions"][region]["definition"]))


    #######################
    #   DATACARD INPUTS   #
    #######################
    # histogram inputs for the datacards
      
    # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
    chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel

    fname   = "%s/%s_%s_tes_$OBS.inputs-%s-%s.root"%(outdir,analysis,chshort,era,tag)

    print "Nominal inputs"
    createinputs(fname, sampleset, observables, bins, filter=setup["processes"], dots=True, parallel=parallel)

    if "TESvariations" in setup:
      for var in setup["TESvariations"]["values"]:
        print "Variation: TES = %f"%var

        newsampleset = sampleset.shift(setup["TESvariations"]["processes"], ("_TES%.3f"%var).replace(".","p"), "_TES%.3f"%var, " %.1d"%((1.-var)*100.)+"% TES", split=True,filter=False,share=True)
        createinputs(fname,newsampleset, observables, bins, filter=setup["TESvariations"]["processes"], dots=True, parallel=parallel)
        newsampleset.close()

    if "systematics" in setup:
      for sys in setup["systematics"]:

        sysDef = setup["systematics"][sys]
        if sysDef["effect"] != "shape":
          continue
        print "Systematic: %s"%sys

        for iSysVar in range(len(sysDef["variations"])):

          sampleAppend = sysDef["sampleAppend"][iSysVar] if "sampleAppend" in sysDef else ""
          weightReplaced = [sysDef["nomWeight"],sysDef["altWeights"][iSysVar]] if "altWeights" in sysDef else ["",""]

          newsampleset_sys = sampleset.shift(sysDef["processes"], sampleAppend, "_"+sysDef["name"]+sysDef["variations"][iSysVar], sysDef["title"], split=True,filter=False,share=True)
          createinputs(fname,newsampleset_sys, observables, bins, filter=sysDef["processes"], replaceweight=weightReplaced, dots=True, parallel=parallel)
          newsampleset_sys.close()

          if "TESvariations" in setup:
            overlap_TES_sys = list( set(sysDef["processes"]) & set(setup["TESvariations"]["processes"]) )
            if overlap_TES_sys:
              for var in setup["TESvariations"]["values"]:
                print "Variation: TES = %f"%var
                newsampleset_TESsys = sampleset.shift(overlap_TES_sys, ("_TES%.3f"%var).replace(".","p")+sampleAppend, "_TES%.3f"%var+"_"+sysDef["name"]+sysDef["variations"][iSysVar], " %.1d"%((1.-var)*100.)+"% TES" + sysDef["title"], split=True,filter=False,share=True)
                createinputs(fname,newsampleset_TESsys, observables, bins, filter=overlap_TES_sys, replaceweight=weightReplaced, dots=True, parallel=parallel)
                newsampleset_TESsys.close()




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
                       ('Nom',      ['ZLL','W','VV','ST','TT','QCD','data_obs'])])
        elif "mutau"in channel:
            varprocs = OrderedDict([
                       ('Nom',      ["ZTT","ZL","ZJ","W","VV","ST","TTT","TTL","TTJ","QCD","data_obs"])])

        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups)
      

if __name__ == "__main__":
  from argparse import ArgumentParser
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','UL2018_v2p5'], default=['UL2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store',
                                         help="set config file containing sample & fit setup" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
