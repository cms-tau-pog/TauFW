#! /usr/bin/env python
"""
Date : May 2022 
Author : @oponcet and Saskia Falke 
Based ond code of Izaak Neutelings (January 2018)
Description : 
Script to generate datacards for the mutau channel and for each regions defined in the config file. 
The tes is defined as a POI for each "tesRegions" defined in the config file. Horizontal morphing is used
to interpolate between the template genrated in "TESvariations" in config file. 
The tid SF is defined as rateParameter for each "tid_SFRegions" defined in the config file.
The autoMCstat function is used to have bin-by-bin uncertainties for the sum of all backgrounds
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

def check_integral(filename, procs, name, region):
   file = TFile(filename)
   ret = []
   name = name.replace('$BIN', region)
   for proc in procs:
     histname = region + '/' + proc + '_' + name
     print(histname, '\t', filename)
     histup = file.Get(histname+'Up').Integral()
     histdn = file.Get(histname+'Down').Integral()
     if histup and histdn: ret.append(proc)
   print('returning: ', name, '\t', ret)
   return ret

def harvest(setup, year, obs, **kwargs):
    """Harvest cards."""

    channel = setup["channel"].replace("mu","m").replace("tau","t")
    
    tag         = kwargs.get('tag',        ""               )
    extratag    = kwargs.get('extratag',   ""               )
    era         = kwargs.get('era',        '%s-13TeV'%year  )
    analysis    = kwargs.get('analysis',   'ztt'            )
    indir       = kwargs.get('indir',      'input_%s'%year  )
    outdir      = indir.replace('input', 'output') #kwargs.get('outdir',     'output_%s'%year )
    outdir      = os.path.join(outdir, year)
    multiDimFit = kwargs.get('multiDimFit')
    verbosity   = kwargs.get('verbosity')
    outtag      = tag+extratag
   
    filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(indir,analysis,channel,obs,era,tag)
 
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

        signals = [] # ZTT is the signal
        backgrounds = []
        for proc in setup["processes"]:
          if "ZTT" in proc:
            signals.append(proc)
          elif not "data" in proc:
            backgrounds.append(proc)
        print("Signals: %s"%signals)
        print("Backgrounds: %s"%backgrounds)

        if("TESvariations" in setup):
          print("Take TESvariations as defined in the config file")
          tesshifts = [ "%.3f"%tes for tes in setup["TESvariations"]["values"] ]
        else:
          print("No TESvariations")
          tesshifts = [ "1.00" ]


        # Creation of the CombineHarvester
        harvester = CombineHarvester()

        # Change flag causing bug : 
        harvester.SetFlag("workspaces-use-clone", True)

        # Add Observation and process
        harvester.AddObservations(['*'], [analysis], [era], [channel], cats)
        harvester.AddProcesses(['*'], [analysis], [era], [channel], backgrounds, cats, False)
        # CAVEAT: Assume we always want to fit TES as POI; if running for mumu channel, everything will be bkg
        harvester.AddProcesses(tesshifts, [analysis], [era], [channel], signals, cats, True)

        print green("\n>>> defining nuissance parameters ...")
  
        if "systematics" in setup:
          for sys in setup["systematics"]:
            sysDef = setup["systematics"][sys]
            scaleFactor = 1.0  
            if "scaleFactor" in sysDef:
              scaleFactor = sysDef["scaleFactor"]
            if "name" in sysDef: sysDef["processes"] = check_integral(filename, sysDef["processes"], sysDef["name"], region)
            harvester.cp().process(sysDef["processes"]).AddSyst(harvester, sysDef["name"] if "name" in sysDef else sys, sysDef["effect"], SystMap()(scaleFactor))
            #print sysDef

        # Adding id SF as a rate parameter affecting the signal ZTT 
        listbin = region.split("_")
        tid_name = "tid_SF"
        # Recommended to define tid_SFRegions in the config file 
        if ("tid_SFRegions" in setup): 
          if region in setup["tid_SFRegions"]:
            tid_name = "tid_SF_%s" %(region)
          else:
              found_match = False
              for bin in listbin:
                #print("bin = %s" %(bin))
                if bin in setup["tid_SFRegions"]:
                  tid_name = "tid_SF_%s" % bin
                  found_match = True
                  break
              if not found_match:
                print('region: ', region)
                print('ERROR : wrong definition of tid_SFRegions for in the config file')
        else: 
          if len(listbin) == 1: # Example : DM
            tid_name = "tid_SF_%s"%(listbin[0]) # tid_SF_DM
          else: # Example : DM_pt
            tid_name = "tid_SF_%s"%(listbin[1]) # tid_SF_pt
        
        print("tid : %s" %(tid_name))
        # Add SF
        harvester.cp().signals().AddSyst(harvester, tid_name,'rateParam', SystMap()(1.00))

        
        # Add W+Jets SF as a free parameter 
        if not "norm_wj" in setup["systematics"]:
          print("W+Jets SF as a free parameter ")
          sf_W = "sf_W_%s"%(region)
          harvester.cp().process(['W']).AddSyst(harvester, sf_W,'rateParam', SystMap()(1.00))
          print(">>>Add sf_W : %s" %(sf_W))
        
        # Add DY cross section as a free parameter. Don't forgot to add Zmm CR !
        if not "xsec_dy" in setup["systematics"]:
          print("DY cross section as a free parameter")
          harvester.cp().process(['ZTT','ZL','ZJ']).AddSyst(harvester, "xsec_dy" ,'rateParam', SystMap()(1.00))

        # Add DY cross section as a free parameter. Don't forgot to add Zmm CR !
        
        # print("muon fake rate free parameter")
        # harvester.cp().process(['ZL', 'TTL']).AddSyst(harvester, "muonFakerate" ,'rateParam', SystMap()(1.00))



        # EXTRACT SHAPES
        print green(">>> extracting shapes...")
        print ">>>   file %s"%(filename)
        ## For now assume that everything that is varied by TES is signal, and everything else is background
        ## Could be revised if wanting to leave the possibility to do other variations or fit normalisation (e.g. for combined TES & ID SF fit)
        harvester.cp().channel([channel]).backgrounds().ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")
        
        # For TES variations 
        if("TESvariations" in setup):
          #print green(">>> TESvariations...")
          harvester.cp().channel([channel]).signals().ExtractShapes(filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
        else:
          harvester.cp().channel([channel]).signals().ExtractShapes(filename, "$BIN/$PROCESS", "$BIN/$PROCESS_$SYSTEMATIC")


   
        # ROOVAR
        workspace = RooWorkspace(analysis,analysis)
        #print analysis

        # Adding TES as a POI the signal ZTT 
        tes_name = "tes"
        # Recommended to define tid_SFRegions in the config file 
        if ("tesRegions" in setup): 
          if region in setup["tesRegions"]:
            tes_name = "tes_%s" %(region)
          else:
              found_match = False
              for bin in listbin:
                #print("bin = %s" %(bin))
                if bin in setup["tesRegions"]:
                  tes_name = "tes_%s" % bin
                  found_match = True
                  break
              if not found_match:
                print("ERROR : wrong definition of tesRegions in the config file ")
        else: 
          tes_name = "tes_%s"%(listbin[0])
        print("tes: %s"%(tes_name))

        if("TESvariations" in setup):
          #print("TESvariations")
          tes = RooRealVar(tes_name,tes_name, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))
        else:
          tes = RooRealVar(tes_name,tes_name, 1.000, 1.000)

        #tes = RooRealVar(tes_name,tes_name, min(setup["TESvariations"]["values"]), max(setup["TESvariations"]["values"]))
        tes.setConstant(True)

    
        # MORPHING
        print green(">>> morphing...")
        BuildCMSHistFuncFactory(workspace, harvester, tes, "ZTT")
    
        #workspace.Print()
        workspace.writeToFile("workspace_py.root")


        # EXTRACT PDFs
        print green(">>> add workspace and extract pdf...")
        harvester.AddWorkspace(workspace, False)
        harvester.ExtractPdfs(harvester, "ztt", "$BIN_$PROCESS_morph", "")  # Extract all processes (signal and bkg are named the same way)
        
        harvester.ExtractData("ztt", "$BIN_data_obs")  # Extract the RooDataHist

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
        if int(verbosity) > 0:
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
        datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s-%s%s-inputs.$ERA.root"%(obs,region,outtag)
        writer = CardWriter(datacardtxt,datacardroot)
        writer.SetVerbosity(verbosity)
        writer.SetWildcardMasses([ ])
        writer.WriteCards(outdir, harvester)
    
        # REPLACE bin ID by bin name
        for region, DM in cats:
          oldfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',str(region)).replace('$ERA',era)
          newfilename = datacardtxt.replace('$TAG',outdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',DM).replace('$ERA',era)
          if os.path.exists(oldfilename):
            os.rename(oldfilename, newfilename)
            print('>>> renaming "%s" -> "%s"'%(oldfilename,newfilename))
          else:
            print('>>> Warning! "%s" does not exist!'%(oldfilename))
        
def scaleProcess(process,scale): 
  """Help function to scale a given process."""
  process.set_rate(process.rate()*scale)
  
def setYield(process,file,dirname,scale=1.):
  """Help function to get yield from file."""
  histname = "%s/%s"%(dirname,process.process()) if dirname else process.process()
  hist = file.Get(histname)
  if not hist:
    print('setYield: Warning! Did not find histogram "%s" in "%s"'%(histname,file.GetName()))
  if hist.GetXaxis().GetNbins()>1:
    print('setYield: Warning! Histogram "%s" has more than one bin!'%(histname))
  rate = hist.GetBinContent(1)
  process.set_rate(rate*scale)
  
def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print(">>> made directory " + dirname)
    return dirname



def main(args):

    ## Open and import information from config file here to be publicly accessible in all functions
    print("Using configuration file: %s"%args.config)
    with open(args.config, 'r') as file:
        setup = yaml.safe_load(file)

    verbosity = 1 if args.verbose else 0
    observables = []
    for obs in setup["observables"]:
        observables.append(obs)
    
    indir = args.input_dir
    if args.multiDimFit:
        args.extratag += "_MDF"

    tag = setup["tag"] if "tag" in setup else ""
    print("producing datacards for %s"%(args.year))
    for obs in observables:
        print("producing datacards for %s"%(obs))
        harvest(setup,args.year,obs,tag=tag,extratag=args.extratag,indir=indir,multiDimFit=args.multiDimFit,verbosity=verbosity)
    



if __name__ == '__main__':

  from argparse import ArgumentParser
  argv = sys.argv
  description = '''This script makes datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
  parser.add_argument('-y', '--year', dest='year', type=str, default=2018, action='store', help="select year")
  parser.add_argument('-c', '--config', dest='config', type=str, default='TauES/config/defaultFitSetupTES_mutau.yml', action='store', help="set config file containing sample & fit setup")
  parser.add_argument('-e', '--extra-tag', dest='extratag', type=str, default="", action='store', metavar='TAG', help="extra tag for output files")
  parser.add_argument('-M', '--multiDimFit', dest='multiDimFit', default=False, action='store_true', help="assume multidimensional fit with a POI for each DM")
  parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true', help="set verbose")
  parser.add_argument('-i', '--input_dir', dest='input_dir', type=str, help='input_dir for datacard root file')
  args = parser.parse_args()

  main(args)
  print(">>>\n>>> done harvesting\n")
    

