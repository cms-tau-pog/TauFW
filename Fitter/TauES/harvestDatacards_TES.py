#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os, sys, re
import yaml
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar


def harvest(setup, year, obs, **kwargs):
    """Harvest cards."""

    channel = setup["channel"].replace("mu","m").replace("tau","t")
    
    tag         = kwargs.get('tag',        ""               )
    extratag    = kwargs.get('extratag',   ""               )
    era         = kwargs.get('era',        '%s-13TeV'%year  )
    analysis    = kwargs.get('analysis',   'ztt'            )
    indir       = kwargs.get('indir',      'input_%s'%year  )
    outdir      = kwargs.get('outdir',     'output_%s'%year )
    multiDimFit = kwargs.get('multiDimFit')
    verbosity   = kwargs.get('verbosity')
    outtag      = tag+extratag
    TIDWP       = 'Medium' if 'Medium' in outtag else 'Tight'
    
    signals = []
    backgrounds = []
    for proc in setup["processes"]:
      if("TESvariations" in setup and proc in setup["TESvariations"]["processes"]):
        signals.append(proc)
      elif not "data" in proc:
        backgrounds.append(proc)
    print "Signals: %s"%signals
    print "Backgrounds: %s"%backgrounds

    cats = []
    icat = 0
    # each variable can have a subset of regions in which it is fitted defined in config file under this variable entry
    if "fitRegions" in setup["observables"][obs]:
      for region in setup["observables"][obs]["fitRegions"]:
        icat += 1
        cats.append((icat, region))
    # if not given, assume all defined regions should be fitted (be careful with potential overlap!)
    elif "regions" in setup:
      for region in setup["regions"]:
        icat += 1
        cats.append((icat,region))
    print "Fit regions for observable %s: %s"%(obs, cats)

    tesshifts = [ "%.3f"%tes for tes in setup["TESvariations"]["values"] ]

    harvester = CombineHarvester()
    harvester.AddObservations(['*'], [analysis], [era], [channel], cats)
    harvester.AddProcesses(['*'], [analysis], [era], [channel], backgrounds, cats, False)
    # CAVEAT: Assume we always want to fit TES as POI; if running for mumu channel, everything will be bkg
    harvester.AddProcesses(tesshifts, [analysis], [era], [channel], signals, cats, True)
    
    # FILTER ## CAVEAT!!! potentially needed to not add zero backgrounds
    #filterDM10      = [ 'STL', 'TTL', 'ZL' ]
    #if filterDM10:
    #  harvester.FilterAll(lambda obj: obj.bin_id() in [3,4] and obj.process() in filterDM10)
    
    # NUISSANCE PARAMETERS
    print green("\n>>> defining nuissance parameters ...")
    
    if "systematics" in setup:
      for sys in setup["systematics"]:
        sysDef = setup["systematics"][sys]
        scaleFactor = 1.0 
        if "scaleFactor" in sysDef: 
          scaleFactor = sysDef["scaleFactor"]
        harvester.cp().process(sysDef["processes"]).AddSyst(harvester, sysDef["name"] if "name" in sysDef else sys, sysDef["effect"], SystMap()(scaleFactor))
 
   
    # EXTRACT SHAPES
    print green(">>> extracting shapes...")
    filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,obs,era,tag)
    print ">>>   file %s"%(filename)
    ## For now assume that everything that is varied by TES is signal, and everything else is background
    ## Could be revised if wanting to leave the possibility to do other variations or fit normalisation (e.g. for combined TES & ID SF fit)
    harvester.cp().channel([channel]).backgrounds().ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
    harvester.cp().channel([channel]).signals().ExtractShapes(filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    #harvester.cp().channel([channel]).process(['proc1','proc2']).ExtractShapes( filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
    
    if "scaleFactors" in setup:
      for SFs in setup["scaleFactors"]:
        print ">>> apply %s normalization factor on the fly on process %s"%(SFs, setup["scaleFactors"][SFs]["processes"])
        for region, sf in setup["scaleFactors"][SFs]["values"][year].iteritems():
          harvester.cp().bin([region]).process(setup["scaleFactors"][SFs]["processes"]).ForEachProc(lambda proc: scaleProcess(proc,sf))
    
    # AUTOREBIN
    #print green(">>> automatically rebin (30%)...")
    #rebin = AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.30).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(1)
    #rebin.Rebin(harvester,harvester)
    
    # BINS
    print green(">>> generating unique bin names...")
    bins = harvester.bin_set() # categories
    #SetStandardBinNames(harvester,"%s_$BINID_$ERA"%(obs))
    
    # Bin-by-bin uncertainties
    if "fitSpecs" in setup and "doBBB" in setup["fitSpecs"] and setup["fitSpecs"]["doBBB"] != "":
      print green(">>> generating bbb uncertainties...")
      procsBBB = backgrounds + signals if ( "signalBBB" in setup["fitSpecs"] and setup["fitSpecs"]["signalBBB"]) else backgrounds
      bbb = BinByBinFactory()
      bbb.SetAddThreshold(0.0)
      bbb.SetFixNorm(False)
      bbb.SetPattern("$PROCESS_bin_$#_$CHANNEL_$BIN")
      bbb.AddBinByBin(harvester.cp().process(procsBBB), harvester)
    
    # ROOVAR
    pois = []
    workspace = RooWorkspace(analysis,analysis)
    if multiDimFit:
      for bin in bins:
        tesname = "tes_%s"%(bin)
        tes = RooRealVar(tesname,tesname, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))
        tes.setConstant(True)
        pois.append(tes)
    else:
      tes = RooRealVar('tes','tes', min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))
      tes.setConstant(True)
      pois = [tes]*len(bins)
    
    # MORPHING
    print green(">>> morphing...")
    debugdir  = ensureDirectory("debug")
    debugfile = TFile("%s/morph_debug_%s_%s_%s%s.root"%(debugdir,year,channel,obs,outtag), 'RECREATE')
    verboseMorph = verbosity>0
    for bin, poi in zip(bins,pois):
      print '>>>   bin "%s"...'%(bin)
      for proc in setup["TESvariations"]["processes"]:
        #print ">>>   bin %s, proc %s"%(bin,proc)
        BuildRooMorphing(workspace, harvester, bin, proc, poi, 'norm', True, verboseMorph, False, debugfile)
    debugfile.Close()
    
    # EXTRACT PDFs
    print green(">>> add workspace and extract pdf...")
    harvester.AddWorkspace(workspace, False)
    harvester.cp().process(setup["TESvariations"]["processes"]).ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")
    
    # NUISANCE PARAMETER GROUPS
    ## To do: export to config file
    print green(">>> setting nuisance parameter groups...")
    harvester.SetGroup( 'bin',      [ ".*_bin_.*"        ])
    harvester.SetGroup( 'lumi',     [ ".*lumi"           ])
    harvester.SetGroup( 'eff',      [ ".*eff_.*"         ])
    harvester.SetGroup( 'jtf',      [ ".*jTauFake.*"     ])
    harvester.SetGroup( 'ltf',      [ ".*mTauFake.*"     ])
    harvester.SetGroup( 'zpt',      [ ".*shape_dy.*"     ])
    harvester.SetGroup( 'xsec',     [ ".*Xsec.*"         ])
    harvester.SetGroup( 'norm',     [ ".*(lumi|Xsec|Norm|norm_qcd).*" ])
    
    # PRINT
    if verbosity>0:
        print green("\n>>> print observation...\n")
        harvester.PrintObs()
        print green("\n>>> print processes...\n")
        harvester.PrintProcs()
        print green("\n>>> print systematics...\n")
        harvester.PrintSysts()
        print green("\n>>> print parameters...\n")
        harvester.PrintParams()
        print "\n"
    
    # WRITER
    print green(">>> writing datacards...")
    datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-$BINID%s-$ERA.txt"%(obs,outtag)
    datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s%s.input-$ERA.root"%(obs,outtag)
    writer = CardWriter(datacardtxt,datacardroot)
    writer.SetVerbosity(verbosity)
    writer.SetWildcardMasses([ ])
    writer.WriteCards(outdir, harvester)
    
    # REPLACE bin ID by bin name
    for bin, DM in cats:
      oldfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',str(bin)).replace('$ERA',era)
      newfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',DM).replace('$ERA',era)
      if os.path.exists(oldfilename):
        os.rename(oldfilename, newfilename)
        print '>>> renaming "%s" -> "%s"'%(oldfilename,newfilename)
      else:
        print '>>> Warning! "%s" does not exist!'%(oldfilename)
    
def scaleProcess(process,scale):
  """Help function to scale a given process."""
  process.set_rate(process.rate()*scale)
  
def setYield(process,file,dirname,scale=1.):
  """Help function to get yield from file."""
  histname = "%s/%s"%(dirname,process.process()) if dirname else process.process()
  hist = file.Get(histname)
  if not hist:
    print 'setYield: Warning! Did not find histogram "%s" in "%s"'%(histname,file.GetName())
  if hist.GetXaxis().GetNbins()>1:
    print 'setYield: Warning! Histogram "%s" has more than one bin!'%(histname)
  rate = hist.GetBinContent(1)
  process.set_rate(rate*scale)
  
def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory " + dirname
    return dirname



def main(args):

    ## Open and import information from config file here to be publicly accessible in all functions
    print "Using configuration file: %s"%args.config
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    verbosity = 1 if args.verbose else 0
    observables = []
    for obs in setup["observables"]:
        observables.append(obs)
    
    indir = "./input"
    if args.multiDimFit:
        args.extratag += "_MDF"

    tag = setup["tag"] if "tag" in setup else ""
    print "producing datacards for %s"%(args.year)
    for obs in observables:
        print "producing datacards for %s"%(obs)
        harvest(setup,args.year,obs,tag=tag,extratag=args.extratag,indir=indir,multiDimFit=args.multiDimFit,verbosity=verbosity)
    



if __name__ == '__main__':

  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script makes datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
  parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], type=str, default=2018, action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
  parser.add_argument('-e', '--extra-tag', dest='extratag', type=str, default="", action='store', metavar='TAG', help="extra tag for output files")
  parser.add_argument('-M', '--multiDimFit', dest='multiDimFit', default=False, action='store_true', help="assume multidimensional fit with a POI for each DM")
  parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true', help="set verbose")
  args = parser.parse_args()

  main(args)
  print ">>>\n>>> done harvesting\n"
    

