#! /usr/bin/env python
"""
Date : June 2022 
Author : @oponcet and Saskia Falke 
Based ond code of Izaak Neutelings (January 2018)
Description : 
Script to generate datacards for the mumu channel and for each regions defined in the config file. 
"""
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True
import os, sys, re
import yaml
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
from CombineHarvester.CombinePdfs.morphing import BuildCMSHistFuncFactory

import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar


def harvest(setup, year, obs, **kwargs):
    """Harvest cards."""

    channel = setup["channel"].replace("mu","m").replace("mu","m")
    
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
    
    # For each region = DM 
    # each variable can have a subset of regions in which it is fitted defined in config file under this variable entry
    if "fitRegions" in setup["observables"][obs]:
      for region in setup["observables"][obs]["fitRegions"]:
        cats = []
        icat = 0
        icat += 1
        cats.append((icat, region))
        # if not given, assume all defined regions should be fitted (be careful with potential overlap!)
        print("region: %s") %(cats)

        signals = []
        backgrounds = []
        for proc in setup["processes"]:
          if "ZTT" in proc:
            signals.append(proc)
          elif not "data" in proc:
            backgrounds.append(proc)
        print "Backgrounds: %s"%backgrounds

   
        harvester = CombineHarvester()

        # Change flag causing bug : 
        harvester.SetFlag("workspaces-use-clone", True)

        harvester.AddObservations(['*'], [analysis], [era], [channel], cats)
        harvester.AddProcesses(['*'], [analysis], [era], [channel], backgrounds, cats, False)
        harvester.AddProcesses(['*'], [analysis], [era], [channel], signals, cats, True)


        print green("\n>>> defining nuissance parameters ...")
  
        if "systematics" in setup:
          for sys in setup["systematics"]:
            sysDef = setup["systematics"][sys]
            scaleFactor = 1.0  
            if "scaleFactor" in sysDef:
              scaleFactor = sysDef["scaleFactor"]
            harvester.cp().process(sysDef["processes"]).AddSyst(harvester, sysDef["name"] if "name" in sysDef else sys, sysDef["effect"], SystMap()(scaleFactor))
   

        # Add DY cross section 
        harvester.cp().process(['ZTT','ZL','ZJ']).AddSyst(harvester, "xsec_dy" ,'rateParam', SystMap()(1.00))


        # EXTRACT SHAPES
        print green(">>> extracting shapes...")
        filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,obs,era,tag)
        print ">>>   file %s"%(filename)
        ## For now assume that everything that is varied by TES is signal, and everything else is background
        ## Could be revised if wanting to leave the possibility to do other variations or fit normalisation (e.g. for combined TES & ID SF fit)
        harvester.cp().channel([channel]).backgrounds().ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
        harvester.cp().channel([channel]).signals().ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
        #harvester.cp().channel([channel]).process(sysDef["processes"]).ExtractShapes( filename, "$BIN/$PROCESS_SF", "$BIN/$PROCESS_$SYSTEMATIC_SF") ###change



   
        # ROOVAR
        workspace = RooWorkspace(analysis,analysis)
        print analysis

    
        #workspace.Print()
        workspace.writeToFile("workspace_py.root")


        # EXTRACT PDFs
        print green(">>> add workspace and extract pdf...")
        harvester.AddWorkspace(workspace, False)        
        harvester.SetAutoMCStats(harvester, 0, 1, 1) # Set the autoMCStats line (with -1 = no bbb uncertainties)



        # NUISANCE PARAMETER GROUPS
        # To do: export to config file
        print green(">>> setting nuisance parameter groups...")
        harvester.SetGroup('all', [ ".*"           ])
        harvester.SetGroup('sys', [ "^((?!bin).)*$"]) # everything except bin-by-bin
        harvester.SetGroup( 'bin',      [ ".*_bin.*"        ])
        harvester.SetGroup( 'lumi',     [ ".*lumi"           ])
        harvester.SetGroup( 'eff',      [ ".*eff_.*"         ])
        harvester.SetGroup( 'jtf',      [ ".*jTauFake.*"     ])
        harvester.SetGroup( 'ltf',      [ ".*mTauFake.*"     ])
        harvester.SetGroup( 'zpt',      [ ".*shape_dy.*"     ])
        harvester.SetGroup( 'xsec',     [ ".*xsec.*"         ])
        harvester.SetGroup( 'norm',     [ ".*(lumi|Xsec|Norm|norm_qcd).*" ])
        harvester.SetGroup( 'tid',      [ ".*tid.*"          ])
        harvester.SetGroup( 'tes',      [ ".*tes.*"          ])


        #PRINT
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
        datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-%s%s-$ERA.txt"%(obs,region,outtag)
        datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s-%s%s.input-$ERA.root"%(obs,region,outtag)
        writer = CardWriter(datacardtxt,datacardroot)
        writer.SetVerbosity(verbosity)
        writer.SetWildcardMasses([ ])
        writer.WriteCards(outdir, harvester)
    
        # REPLACE bin ID by bin name
        for region, DM in cats:
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



def main(args):

    ## Open and import information from config file here to be publicly accessible in all functions
    print "Using configuration file: %s"%args.config
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    verbosity = 1 if args.verbose else 0
    observables = []
    for obs in setup["observables"]:
        observables.append(obs)
    
    indir = "./input_pt_nbin6_moretes"
    if args.multiDimFit:
        args.extratag += "_MDF"

    tag = setup["tag"] if "tag" in setup else ""
    print "producing datacards for %s"%(args.year)
    for obs in observables:
        print "producing datacards for %s"%(obs)
        harvest(setup,args.year,obs,tag=tag,extratag=args.extratag,indir=indir,outdir=args.output_dir,multiDimFit=args.multiDimFit,verbosity=verbosity)
    



if __name__ == '__main__':

  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script makes datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
  parser.add_argument('-y', '--year', dest='year', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018','UL2018_v10','2022_postEE','2022_preEE', '2023C', '2023D'], type=str, default=2018, action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
  parser.add_argument('-e', '--extra-tag', dest='extratag', type=str, default="", action='store', metavar='TAG', help="extra tag for output files")
  parser.add_argument('-M', '--multiDimFit', dest='multiDimFit', default=False, action='store_true', help="assume multidimensional fit with a POI for each DM")
  parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true', help="set verbose")
  parser.add_argument('-o', '--output_dir', dest='output_dir', help="outputdir")
  args = parser.parse_args()

  main(args)
  print ">>>\n>>> done harvesting\n"
    

