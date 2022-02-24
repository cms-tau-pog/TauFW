#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os, sys, re
from argparse import ArgumentParser
import yaml
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar

argv = sys.argv
description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
parser.add_argument('-y', '--year',        dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], type=str, default=2018, action='store',
                                           help="select year")
parser.add_argument('-c', '--channel',     dest='channels', choices=['mt','et'], type=str, nargs='+', default='mt', action='store',
                                           help="channels to submit")
parser.add_argument('-f', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store',
                                         help="set config file containing sample & fit setup" )
parser.add_argument('-t', '--tag',         dest='tags', type=str, nargs='+', default=[ ], action='store',
                    metavar='TAG',         help="tag for a file names")
parser.add_argument('-e', '--extra-tag',   dest='extratag', type=str, default="", action='store',
                    metavar='TAG',         help="extra tag for output files")
parser.add_argument('-o', '--obs',         dest='observables', type=str, nargs='*', default=[ ], action='store',
                    metavar='VARIABLE',    help="name of observable for TES measurement" )
parser.add_argument('-r', '--shift-range', dest='shiftRange', type=str, default="0.940,1.060", action='store',
                    metavar='RANGE',       help="range of TES shifts")
parser.add_argument('-n', '--no-shapes',   dest='noShapes', default=False, action='store_true',
                                           help="do not include shape uncertainties")
parser.add_argument('-M', '--multiDimFit', dest='multiDimFit', default=False, action='store_true',
                                           help="assume multidimensional fit with a POI for each DM")
parser.add_argument('-C', '--ZMM',         dest='ZMM', default=False, action='store_true',
                                           help="include ZMM control region")
parser.add_argument('-v', '--verbose',     dest='verbose',  default=False, action='store_true',
                                           help="set verbose")
args = parser.parse_args()

## Open and import information from config file here to be publicly accessible in all functions
print "Using configuration file: %s"%args.config
with open(args.config, 'r') as file:
  setup = yaml.safe_load(file)

verbosity       = 1 if args.verbose else 0
doShapes        = not args.noShapes #and False
doBBB           = doShapes #and False
signalBBB       = True #and False
multiDimFit     = args.multiDimFit
morphQCD        = True and False
doFR            = True and False
observables     = [o for o in args.observables if '#' not in o]
filterDM10      = [ 'STL', 'TTL', 'ZL' ] # 'ZL', 'ZJ' ] #'ZJ',
scaleDM0        = 1. #0.99/0.90
WNFs            = {
 'UL2016_preVFP':   { 'DM0': 0.939,  'DM1': 1.031,  'DM10': 1.065,  'DM11': 1.021  },
 'UL2016_postVFP':  { 'DM0': 0.919,  'DM1': 0.972,  'DM10': 1.112,  'DM11': 1.074  },
 'UL2017':          { 'DM0': 0.971,  'DM1': 0.995,  'DM10': 1.109,  'DM11': 1.075  },
 'UL2018':          { 'DM0': 1.007,  'DM1': 0.968,  'DM10': 1.079,  'DM11': 1.044  },
   '2016':          { 'DM0': 0.796,  'DM1': 0.913,  'DM10': 1.075,  'DM11': 1.025  },
   '2017':          { 'DM0': 0.962,  'DM1': 0.970,  'DM10': 1.006,  'DM11': 0.919  },
   '2018':          { 'DM0': 1.045,  'DM1': 1.033,  'DM10': 1.193,  'DM11': 1.033  },
}
TIDSFs          = {
#   2016: { 'Medium': { 'DM0': 0.9599, 'DM1': 0.9191, 'DM10': 0.8733, 'DM11': 0.8547 },
#           'Tight':  { 'DM0': 0.8988, 'DM1': 0.9134, 'DM10': 0.8556, 'DM11': 0.8323 }, },
#   2017: { 'Medium': { 'DM0': 0.9306, 'DM1': 0.9062, 'DM10': 0.8603, 'DM11': 0.7967 },
#           'Tight':  { 'DM0': 0.9098, 'DM1': 0.8902, 'DM10': 0.8403, 'DM11': 0.7670 }, },
#   2018: { 'Medium': { 'DM0': 0.9815, 'DM1': 0.9096, 'DM10': 0.9353, 'DM11': 0.8893 },
#           'Tight':  { 'DM0': 0.9741, 'DM1': 0.9144, 'DM10': 0.9123, 'DM11': 0.8606 }, },
}


def harvest(channel,var,year,**kwargs):
    """Harvest cards."""
    
    tag         = kwargs.get('tag',        ""               )
    extratag    = kwargs.get('extratag',   ""               )
    era         = kwargs.get('era',        '%s-13TeV'%year  )
    analysis    = kwargs.get('analysis',   'ztt'            )
    indir       = kwargs.get('indir',      'input_%s'%year  )
    outdir      = kwargs.get('outdir',     'output_%s'%year )
    outtag      = tag+extratag
    TIDWP       = 'Medium' if 'Medium' in outtag else 'Tight'
    
    procs    = {
        'sig':   [ 'ZTT' ],
        'bkg':   [ 'ZL', 'ZJ', 'TTT', 'TTL', 'TTJ', 'W', 'QCD', 'ST', 'VV' ],
        'noQCD': [ 'ZL', 'ZJ', 'TTT', 'TTL', 'TTJ', 'W',        'ST', 'VV' ],
        'DY':    [ 'ZTT', 'ZL', 'ZJ' ],
        'TT':    [ 'TTT', 'TTL', 'TTJ' ],
        'ST':    [ 'STT', 'STJ' ],
        'mumu':  [ 'ZMM', 'W', 'VV', 'TT', 'ST' ],
    }
    
    signal = []
    bkg = []
    for proc in setup["processes"]:
      if("TESvariations" in setup and proc in setup["TESvariations"]["processes"]):
        signal.append(proc)
      else:
        bkg.append(proc)


    cats = []
    icat = 0
    # each variable can have a subset of regions in which it is fitted
    # defined in config file under this variable entry
    if "fitRegions" in setup["observables"][var]:
      for region in setup["observables"][var]["fitRegions"]:
        icat += 1
        cats.append((icat, region))
    # if not given, assume all defined regions should be fitted 
    # (be careful with potential overlap!)
    elif "regions" in setup:
      for region in setup["regions"]:
        icat += 1
        cats.append((icat,region))

    print "Fit regions for observable %s: %s"%(var, cats)

    harvester = CombineHarvester()
    harvester.AddObservations(['*'], [analysis], [era], [channel], cats)
    harvester.AddProcesses(['*'], [analysis], [era], [channel], procs['bkg'], cats, False)
    # CAVEAT: This is specific to mutau channel; should see how to generalise!
    tesshifts = [ "%.3f"%tes for tes in setup["TESvariations"]["values"] ]
    harvester.AddProcesses(tesshifts, [analysis], [era], [channel], procs['sig'], cats, True)
    
    # FILTER ## CAVEAT!!! potentially needed to not add zero backgrounds
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
 
      # CAVEAT!!!? Option in config file to apply some systematics only to some observables?    
      #      if 'm_vis' in var:
      #        harvester.cp().process(['ZL','TTL']).bin(['DM0','DM1']).AddSyst( #,'STJ'
      #          harvester, 'shape_mTauFake_$BIN', 'shape', SystMap()(1.00))
      #      harvester.cp().process(['ZL','TTL']).bin(['DM0','DM1']).AddSyst( #,'STJ'
      #        harvester, 'shape_mTauFakeSF', 'shape', SystMap()(1.00))
      
   
    # EXTRACT SHAPES
    print green(">>> extracting shapes...")
    filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,var,era,tag)
    print ">>>   file %s"%(filename)
    if morphQCD:
      harvester.cp().channel([channel]).process(procs['noQCD']).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(     ['QCD']  ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals(              ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    elif doFR:
      harvester.cp().channel([channel]).backgrounds().ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals().ExtractShapes(     filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    else:
      #harvester.cp().channel([channel]).backgrounds(          ).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(procs['noQCD']).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(     ['QCD']  ).ExtractShapes( filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
      #harvester.cp().channel([channel]).process(     ['QCD']  ).ExtractShapes( filename, "$BIN/$PROCESS_TES1.000", "$BIN/$PROCESS_TES1.000_$SYSTEMATIC")
      #harvester.cp().channel([channel]).signals(              ).ExtractShapes( filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals(              ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    
    # SCALE W on the fly
    print ">>> apply W normalization factor on the fly"
    if WNFs:
      for dm, sf in WNFs[year].iteritems():
        harvester.cp().bin([dm]).process(['W']).ForEachProc(lambda proc: scaleProcess(proc,sf))
    #### SCALE on the fly
    ###print ">>> apply tau ID SF for '%s' WP on the fly"%(TIDWP)
    ###if TIDSFs:
    ###  for dm, sf in TIDSFs[year][TIDWP].iteritems():
    ###    harvester.cp().bin([dm]).process(['ZTT','TTT','STT']).ForEachProc(lambda proc: scaleProcess(proc,sf))
    ###  #if scaleDM0!=1.0:
    ###  #  harvester.cp().process(['ZTT','TTT','STT']).bin_id([1]).ForEachProc(lambda proc: scaleProcess(proc,scaleDM0))
    
    # AUTOREBIN
    #print green(">>> automatically rebin (30%)...")
    #rebin = AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.30).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(1)
    #rebin.Rebin(harvester,harvester)
    
    # BINS
    print green(">>> generating unique bin names...")
    bins = harvester.bin_set() # categories
    #SetStandardBinNames(harvester,"%s_$BINID_$ERA"%(var))
    
    # BIN NAMES
    if doBBB:
      print green(">>> generating bbb uncertainties...")
      procsBBB = procs['bkg'] + procs['sig'] if signalBBB else procs['bkg']
      bbb = BinByBinFactory()
      bbb.SetAddThreshold(0.0)
      bbb.SetFixNorm(False)
      bbb.SetPattern("$PROCESS_bin_$#_$CHANNEL_$BIN")
      bbb.AddBinByBin(harvester.cp().process(procsBBB), harvester)
      ###bbb.MergeBinErrors(harvester.cp().process(procs['sig'] + ['W', 'QCD', 'ZJ', 'ZL']))
      ###bbb.SetMergeThreshold(0.0)
    
    # ROOVAR
    pois = [ ]
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
    debugfile = TFile("%s/morph_debug_%s_%s_%s%s.root"%(debugdir,year,channel,var,outtag), 'RECREATE')
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
    print green(">>> setting nuisance parameter groups...")
    ###harvester.SetGroup( 'all',      [ ".*"               ])
    harvester.SetGroup( 'bin',      [ ".*_bin_.*"        ])
    ###harvester.SetGroup( 'sys',      [ "^((?!bin).)*$"    ]) # everything except bin-by-bin
    harvester.SetGroup( 'lumi',     [ ".*lumi"           ])
    harvester.SetGroup( 'eff',      [ ".*eff_.*"         ])
    harvester.SetGroup( 'jtf',      [ ".*jTauFake.*"     ])
    harvester.SetGroup( 'ltf',      [ ".*mTauFake.*"     ])
    harvester.SetGroup( 'zpt',      [ ".*shape_dy.*"     ])
    harvester.SetGroup( 'xsec',     [ ".*Xsec.*"         ])
    harvester.SetGroup( 'norm',     [ ".*(lumi|Xsec|Norm|norm_qcd).*" ])
    #harvester.RemoveGroup(  "syst", [ "lumi_.*" ])
    
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
    datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-$BINID%s-$ERA.txt"%(var,outtag)
    datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s%s.input-$ERA.root"%(var,outtag)
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
    


def harvest_ZMM(year,**kwargs):
    """Harvest ZMM cards."""
    
    var      = 'm_vis'
    channel  = 'mm'
    tag      = kwargs.get('tag',      ""               )
    extratag = kwargs.get('extratag', ""               )
    era      = kwargs.get('era',      '%s-13TeV'%year  )
    analysis = kwargs.get('analysis', 'ztt'            )
    indir    = kwargs.get('indir',    'input_%s'%year  )
    outdir   = kwargs.get('outdir',   'output_%s'%year )
    
    cats     = [ (5, 'ZMM') ]
    procs    = {
        'sig':   [ 'ZMM' ],
        'bkg':   [ 'ZMM', 'W', 'VV', 'TT', 'ST' ],
    }
    
    # HARVESTER
    harvester = CombineHarvester()
    harvester.AddObservations( ['*'], [analysis], [era], [channel],               cats         )
    harvester.AddProcesses(    ['*'], [analysis], [era], [channel], procs['bkg'], cats, False  )
    
    # NUISSANCE PARAMETERS
    print green("\n>>> defining nuissance parameters ...")
    
    harvester.cp().process('ZMM').AddSyst(
        harvester, 'lumi', 'lnN', SystMap()(1.025))
    
    harvester.cp().process('ZMM').AddSyst(
        harvester, 'eff_m', 'lnN', SystMap()(1.02))
    
    harvester.cp().process('ZMM').AddSyst(
        harvester, 'xsec_dy', 'lnN', SystMap()(1.02))
    
    #harvester.cp().process(['W']).AddSyst(
    #    harvester, 'norm_wj', 'lnN', SystMap()(1.15))
    #
    #harvester.cp().process(procs['TT']).AddSyst(
    #    harvester, 'xsec_tt', 'lnN', SystMap()(1.06))
    #
    #harvester.cp().process(procs['ST']).AddSyst(
    #    harvester, 'xsec_st', 'lnN', SystMap()(1.05))
    #
    #harvester.cp().process(['VV']).AddSyst(
    #    harvester, 'xsec_vv', 'lnN', SystMap()(1.05))
    
    # NUISANCE PARAMETER GROUPS
    print green(">>> setting nuisance parameter groups...")
    harvester.SetGroup( 'all',      [ ".*"               ])
    harvester.SetGroup( 'sys',      [ "^((?!bin).)*$"    ]) # everything except bin-by-bin
    harvester.SetGroup( 'lumi',     [ ".*_lumi"          ])
    
    # GET YIELDS
    scale    = 1e-3 # scale to prevent issues with large number
    dirname  = cats[0][1]
    filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,var,era,tag)
    file = TFile.Open(filename,'READ')
    if not file:
      print 'harvest_ZMM: Warning! Did not find file "%s"'%(filename)
    harvester.cp().ForEachObs(lambda proc: setYield(proc,file,dirname=dirname,scale=scale))
    harvester.cp().ForEachProc(lambda proc: setYield(proc,file,dirname=dirname,scale=scale))
    
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
    cardname = "%s/%s_%s_%s-%s%s-%s.txt"%(outdir,analysis,channel,var,cats[0][1],outtag,era)
    print ">>> %s"%cardname
    harvester.WriteDatacard(cardname)
    #datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-$BINID%s-$ERA.txt"%(var,outtag)
    #datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s%s.input-$ERA.root"%(var,outtag)
    #writer = CardWriter(datacardtxt,datacardroot)
    #writer.SetVerbosity(verbosity)
    #writer.SetWildcardMasses([ ])
    #writer.WriteCards(outdir, harvester)
    
    ## REPLACE bin ID by bin name
    #for bin, DM in cats:
    #  oldfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',str(bin)).replace('$ERA',era)
    #  newfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',DM).replace('$ERA',era)
    #  if os.path.exists(oldfilename):
    #    os.rename(oldfilename, newfilename)
    #    print '>>> renaming "%s" -> "%s"'%(oldfilename,newfilename)
    #  else:
    #    print '>>> Warning! "%s" does not exist!'%(oldfilename)
    


def scaleProcess(process,scale):
  """Help function to scale a given process."""
  #print '>>> scaleProcess("%s",%.3f):'%(process.process(),scale)
  #print ">>>   rate before = %s"%(process.rate())
  process.set_rate(process.rate()*scale)
  #print ">>>   rate after  = %s"%(process.rate())
  
def setYield(process,file,dirname,scale=1.):
  """Help function to get yield from file."""
  histname = "%s/%s"%(dirname,process.process()) if dirname else process.process()
  hist = file.Get(histname)
  if not hist:
    print 'setYield: Warning! Did not find histogram "%s" in "%s"'%(histname,file.GetName())
  if hist.GetXaxis().GetNbins()>1:
    print 'setYield: Warning! Histogram "%s" has more than one bin!'%(histname)
  rate = hist.GetBinContent(1)
  #print process.process(), histname, rate
  process.set_rate(rate*scale)
  
def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory " + dirname
    return dirname



def main():
    
    channels = [ 'mt', ] #'et', ]
    vars     = [ 'm_2', 'm_vis', ]
    
    year     = args.year
    vars     = observables if observables else vars
    indir    = "./input"
    #indir    = "./input_%s"%(args.year)
    extratag = args.extratag
    if multiDimFit:
      extratag += "_MDF"
    
    print "We need a tag!!!!!!!!!!!!!"
    for tag in args.tags:
      vars2 = vars[:]
      if "_0p"  in tag: vars2 = [ v for v in vars2 if v!='m_vis' ]
      if "_45"  in tag: vars2 = [ v for v in vars2 if v!='m_2'   ]
      if "_100" in tag: vars2 = [ v for v in vars2 if v!='m_2'   ]
      if "_200" in tag: vars2 = [ v for v in vars2 if v!='m_2'   ]
      
      print "producing datacards for %s"%(year)
      for channel in channels:
        print "producing datacards for %s"%(channel)
        for var in vars2:
          print "producing datacards for %s"%(var)
          harvest(channel,var,year,tag=tag,extratag=extratag,indir=indir)
    
    if args.ZMM:
      harvest_ZMM(year,indir=indir,verbosity=2)
    


if __name__ == '__main__':
    main()
    print ">>>\n>>> done harvesting\n"
    

