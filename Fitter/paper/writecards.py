#! /usr/bin/env python
# Author: Izaak Neutelings (Februari 2021)
import os, sys, re
from TauFW.common.tools.file import ensuredir, ensureTFile, ensureTDirectory
from TauFW.common.tools.utils import repkey
from TauFW.Plotter.plot.utils import LOG
from argparse import ArgumentParser
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar
argv = sys.argv
description = '''This script creates datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvestercards",description=description,epilog="Succes!")
parser.add_argument('-y', '--era',      dest='eras', nargs='*', choices=['2016','2017','2018','UL2017'], default=['UL2017'], action='store',
                                        help="set era" )
parser.add_argument('-c', '--channel',  dest='channels', choices=['mt','et'], type=str, nargs='+', default=['mt'], action='store',
                                        help="channels to submit")
parser.add_argument('-t', '--tag',      dest='tags', type=str, nargs='+', default=[""], action='store',
                    metavar='TAG',      help="tag for input and output file names")
parser.add_argument('-e', '--outtag',   dest='outtag', type=str, default="", action='store',
                    metavar='TAG',      help="extra tag for output files")
parser.add_argument('-o', '--obs',      dest='observables', type=str, nargs='*', default=[ 'mvis' ], action='store',
                    metavar='VARIABLE', help="name of observable" )
parser.add_argument('-n', '--noshapes', dest='noshapes', default=False, action='store_true',
                                        help="do not include shape uncertainties")
parser.add_argument('-v', '--verbose',  dest='verbose',  default=False, action='store_true',
                                        help="set verbose")
args = parser.parse_args()
verbosity = 1 if args.verbose else 0
doshapes  = not args.noshapes #and False # do not include shapes
dobbb     = doshapes #and False          # do bin-by-bin uncertainties
#from createinputs import tauidsfs # 2017 DM-dependent tau eff. SF


def harvest(obs,channel,era,**kwargs):
  """Harvest cards."""
  print ">>>\n>>> %s, %s, %s"%(obs,channel,era)
  tag      = kwargs.get('tag',     ""            ) # tag for input and output file names
  outtag   = kwargs.get('outtag',  ""            ) # extra tag for output file names
  analysis = kwargs.get('analysis','ztt_tid'     )
  indir    = kwargs.get('indir',   'input'       )
  outdir   = kwargs.get('outdir',  'output/$ERA' )
  infile   = "$INDIR/$ANALYSIS_$OBS_$CHANNEL-$ERA$TAG.inputs.root"
  infile   = repkey(infile,INDIR=indir,ANALYSIS=analysis,OBS=obs,CHANNEL=channel,ERA=era,TAG=tag)
  outcard  = "$TAG/$ANALYSIS_%s_$CHANNEL-$BINID-$ERA%s.datacard.txt"%(obs,tag+outtag)
  outfile  = "$TAG/$ANALYSIS_%s_$CHANNEL-$ERA%s.inputs.root"%(obs,tag+outtag)
  indir    = repkey(indir,ERA=era,CHANNEL=channel)
  outdir   = repkey(outdir,ERA=era,CHANNEL=channel)
  
  # HARVESTER
  cats = [ # categories "bins"
    'Tight'
  ]
  procs = { # processes
    'sig':   [ 'ZTT' ],
    'bkg':   [ 'ZL', 'ZJ', 'TTT', 'TTJ', 'W', 'QCD', 'ST', 'VV' ],
    'noQCD': [ 'ZL', 'ZJ', 'TTT', 'TTJ', 'W',        'ST', 'VV' ],
    'DY':    [ 'ZTT', 'ZL', 'ZJ' ],
    'TT':    [ 'TTT', 'TTJ' ],
    'ST':    [ 'ST' ], #'STT', 'STJ' ],
    'tau':   [ 'ZTT', 'TTT' ], #'STT'
  }
  procs['all'] = procs['sig'] + procs['bkg']
  if "mtau" in obs: # split ZTT into DMs
    for key, plist in procs.iteritems():
      if 'ZTT' in plist:
        idx = plist.index('ZTT')
        procs[key] = plist[:idx]+['ZTT_DM0','ZTT_DM1','ZTT_DM10','ZTT_DM11']+plist[idx+1:] # insert
  cats = [c for c in enumerate(cats,1)] # autmatically number; ($BINID,$BIN)
  harvester = CombineHarvester()
  harvester.AddObservations(['*'], [analysis],[era],[channel],             cats      )
  harvester.AddProcesses(   ['*'], [analysis],[era],[channel],procs['bkg'],cats,False)
  harvester.AddProcesses(   ['90'],[analysis],[era],[channel],procs['sig'],cats,True )
  #harvester.FilterAll(lambda obj: obj.process() in ['QCD','W','ZJ','STJ'] )
  
  # NORM NUISSANCE PARAMETERS
  LOG.color("Defining nuissance parameters ...")
  
  harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
    harvester, 'lumi', 'lnN', SystMap()(1.025)) # luminosity
  
  harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
    harvester, 'eff_trig', 'lnN', SystMap()(1.02)) # trigger efficiency
  
  harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
    harvester, 'eff_m', 'lnN', SystMap()(1.02)) # muon efficiency
  
  #if 'mtau' in obs:
  #  for dm in [0,1,10,11]:
  #    sf, err = tauidsfs[era][dm]
  #    harvester.cp().process(['ZTT_DM%d'%dm]).AddSyst(
  #      harvester, 'eff_t_dm%s'%dm, 'lnN', SystMap()(1.+err/sf)) # tau eff. SF (DM-dependent)
  #else:
  #  harvester.cp().process(procs['tau']).AddSyst(
  #    harvester, 'eff_t', 'lnN', SystMap()(1.20)) # tau efficiency
  
  ###harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
  ###  harvester, 'eff_tracking', 'lnN', SystMap()(1.04))
  
  harvester.cp().process(['W']).AddSyst(
    harvester, 'norm_w', 'lnN', SystMap()(1.15)) # W+jets xsec
  
  harvester.cp().process(['QCD']).AddSyst(
    harvester, 'norm_qcd', 'lnN', SystMap()(1.20)) # QCD xsec
  
  harvester.cp().process(procs['DY']).AddSyst(
    harvester, 'xsec_dy', 'lnN', SystMap()(1.02)) # Drell-Yan xsec
  
  harvester.cp().process(procs['TT']).AddSyst(
    harvester, 'xsec_tt', 'lnN', SystMap()(1.06)) # ttbar xsec
  
  harvester.cp().process(procs['ST']).AddSyst(
    harvester, 'xsec_st', 'lnN', SystMap()(1.05)) # single top xsec
  
  harvester.cp().process(['VV']).AddSyst(
    harvester, 'xsec_vv', 'lnN', SystMap()(1.05)) # diboson xsec
  
  harvester.cp().process(['ZL','TTL','STL']).AddSyst(
    harvester, 'rate_ltf', 'lnN', SystMap()(1.25)) # l -> tau fake rate
  
  # SHAPE NUISSANCE PARAMETERS
  harvester.cp().process(['W','QCD','ZJ','TTJ','STJ']).AddSyst(
    harvester, 'rate_jtf', 'lnN', SystMap()(1.25)) # j -> tau fake rate
  
  if doshapes:
    harvester.cp().process(['ZJ','W','QCD']).AddSyst( #'ZJ','TTJ','STJ'
      harvester, 'shape_jtf', 'shape', SystMap()(1.00)) # j -> tau fake energy scale
    
    harvester.cp().process(procs['tau']).AddSyst( #['TTT','STT']
      harvester, 'shape_tid', 'shape', SystMap()(1.00)) # tau eff. SF
    if 'mtau' not in obs:
      harvester.cp().process(['ZL']).AddSyst( #bin_id([1,2])
        harvester, 'shape_ltf', 'shape', SystMap()(1.00)) # l -> tau fake energy scale
    
    harvester.cp().process(procs['DY']).AddSyst(
      harvester, 'shape_dy', 'shape', SystMap()(1.00)) # Z pT reweighting
    
    #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
    #  harvester, 'shape_jes', 'shape', SystMap()(1.00)) # jet energy scale
    
    #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
    #  harvester, 'shape_jer', 'shape', SystMap()(1.00)) # jet energy resolution
    
    #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
    #  harvester, 'shape_uncEn', 'shape', SystMap()(1.0)) # unclustered energy
  
  # EXTRACT SHAPES
  LOG.color("Extracting shapes...")
  print ">>>   file %r"%(infile)
  harvester.cp().channel([channel]).ExtractShapes(infile,"$BIN/$PROCESS","$BIN/$PROCESS_$SYSTEMATIC")
  
  ## RESCALE on the fly
  #if 'mtau' in obs:
  #  for dm in [0,1,10,11]:
  #    sf, err = tauidsfs[era][dm]
  #    harvester.cp().process(['ZTT_DM%d'%dm]).ForEachProc(lambda p: scaleproc(p,sf))
  
  # AUTOREBIN
  #LOG.color("automatically rebin (30%)...")
  #rebin = AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.30).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(1)
  #rebin.Rebin(harvester,harvester)
  
  # BINS
  LOG.color("Generating unique bin names...")
  bins = harvester.bin_set()
  #SetStandardBinNames(harvester,"%s_$BINID_$ERA"%(obs))
  
  # BIN NAMES
  if dobbb:
    LOG.color("Generating bbb uncertainties...")
    bbb = BinByBinFactory()
    bbb.SetAddThreshold(0.0)
    bbb.SetFixNorm(False)
    bbb.SetPattern("$PROCESS_bin_$#_$CHANNEL_$BIN")
    bbb.AddBinByBin(harvester,harvester)
    ###bbb.MergeBinErrors(harvester.cp().process(procs['sig'] + ['W', 'QCD', 'ZJ', 'ZL']))
    ###bbb.SetMergeThreshold(0.0)
  
  # NUISANCE PARAMETER GROUPS
  LOG.color("Setting nuisance parameter groups...")
  harvester.SetGroup('all', [ ".*"           ])
  harvester.SetGroup('bin', [ ".*_bin_.*"    ])
  harvester.SetGroup('sys', [ "^((?!bin).)*$"]) # everything except bin-by-bin
  harvester.SetGroup('lumi',[ ".*lumi"       ])
  harvester.SetGroup('xsec',[ ".*Xsec.*"     ])
  harvester.SetGroup('eff', [ ".*eff_.*"     ])
  harvester.SetGroup('norm',[ ".*(lumi|xsec|norm|eff).*" ])
  harvester.SetGroup('jtf', [ ".*jtf.*" ])
  harvester.SetGroup('ltf', [ ".*ltf.*" ])
  harvester.SetGroup('es',  [ ".*shape_(tes|[eml]tf|jes)_.*"])
  harvester.SetGroup('zpt', [ ".*shape_dy.*" ])
  
  # PRINT
  if verbosity>=1:
    LOG.color("\n>>> print observation...\n")
    harvester.PrintObs()
    LOG.color("\n>>> print processes...\n")
    harvester.PrintProcs()
    LOG.color("\n>>> print systematics...\n")
    harvester.PrintSysts()
    LOG.color("\n>>> print parameters...\n")
    harvester.PrintParams()
    print "\n"
  
  # WRITE CARDS
  LOG.color("Writing datacards...")
  writer = CardWriter(outcard,outfile)
  writer.SetVerbosity(verbosity)
  writer.SetWildcardMasses([ ])
  writer.WriteCards(outdir,harvester)
  
  # REPLACE bin ID by bin name
  for bin, cat in cats:
    oldfilename = repkey(outcard,TAG=outdir,ANALYSIS=analysis,CHANNEL=channel,ERA=era,BINID=str(bin))
    newfilename = repkey(outcard,TAG=outdir,ANALYSIS=analysis,CHANNEL=channel,ERA=era,BINID=cat)
    if os.path.exists(oldfilename):
      os.rename(oldfilename,newfilename)
      print '>>> Renaming "%s" -> "%s"'%(oldfilename,newfilename)
    else:
      print '>>> Warning! "%s" does not exist!'%(oldfilename)
  

def scaleproc(proc,scale):
  """Help function to scale a given process."""
  proc.set_rate(proc.rate()*scale)
  

def main():
  obsset   = [o for o in args.observables if '#' not in o]
  channels = args.channels
  eras     = args.eras
  indir    = "./input"
  outtag   = args.outtag
  for tag in args.tags:
    for era in eras:
      for channel in channels:
        for obs in obsset:
          harvest(obs,channel,era,tag=tag,outtag=outtag,indir=indir)
  

if __name__ == '__main__':
  print
  main()
  print ">>>\n>>> Done harvesting\n"
  
