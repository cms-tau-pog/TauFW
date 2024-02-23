#! /usr/bin/env python
# Author: Yuta Takahashi & Izaak Neutelings (January 2018) edited by Paola Mastrapasqua(Feb 2024)
import os #, sys, re
from argparse import ArgumentParser
from CombineHarvester.CombineTools import ch
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True


def main(args):
  
  # SETTINGS
  filename_mt = args.filename_mt # SR
  #filename_mm = args.filename_mm # CR
  outdir      = "cards"
  wp          = args.wp
  era         = args.era
  tag         = args.tag
  doshapes    = args.doshapes 
  verbosity   = args.verbosity
  if verbosity>=1:
    print(">>> filename_mt = %r"%(filename_mt))
    print(">>> filename_mm = %r"%(filename_mm))
    print(">>> wp          = %r"%(wp))
    print(">>> era         = %r"%(era))
    print(">>> tag         = %r"%(tag))
    print(">>> method      = %r"%(method))
    print(">>> doshapes    = %r"%(doshapes))
  
  # PROCESSES
  procs = {
    'sig': {
      'mt':['ZTT'],
      #'mm':['ZLL']
    },
    'bkg': {
      'mt': ['TTT','TTJ','TTL','ZL','ST','VV'],
      #'mm': ['TT','W','ST','VV','QCD'],
    }
  }
  procs['bkg']['mt'].extend(['ZJ','W','QCD'])
  if verbosity>=1:
    print(">>> procs['sig'] = %r"%(procs['sig']))
    print(">>> procs['bkg'] = %r"%(procs['bkg']))
  
  # CATEGORIES
  #channels = ['mt', 'mm']
  channels = ['mt']
  categories = {
    'mt': [(0,wp)],
    #'mm': [(1,'ZMM')],
  }
  files = {
    'mt': filename_mt,
    #'mm': filename_mm,
  }
  
  # HARVESTER
  cb = ch.CombineHarvester()
  for chn in channels:
    ana  = ['ztt']
    eras = [era]
    cb.AddObservations(['*'],ana,eras,[chn],categories[chn])
    cb.AddProcesses(['*'], ana,eras,[chn],procs['bkg'][chn],categories[chn], False)
    cb.AddProcesses(['90'],ana,eras,[chn],procs['sig'][chn],categories[chn], True )
  print('>> Add systematics...')
  cb.cp().AddSyst(
    cb, 'CMS_lumi', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ'] + procs['sig']['mt'],                    1.025)
      #(['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.025)
      )
  cb.cp().AddSyst(
    cb, 'CMS_eff_m', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ']  + procs['sig']['mt'],                    1.02)
      #(['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.04)
      )
  cb.cp().AddSyst(
    cb, 'CMS_trig_m', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ'] + procs['sig']['mt'],                    1.02)
      #(['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.02)
      )
  cb.cp().AddSyst(
    cb, 'CMS_ttxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL'],             1.055)
      #(['mm'], ['TT'],             1.055)
      )
  cb.cp().AddSyst(
    cb, 'CMS_stxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['ST'],             1.055)
      #(['mm'], ['ST'],             1.055)
      )
  cb.cp().AddSyst(
    cb, 'CMS_vvxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['VV'],             1.06)
      #(['mm'], ['VV'],             1.06)
      )
  cb.cp().AddSyst(
    cb, 'CMS_dyxsec', 'rateParam', ch.SystMap('channel','process')
      (['mt'], ['ZTT', 'ZJ', 'ZL'], 1.0)
      #(['mm'], ['ZLL'],             1.0)
      )
  
  cb.cp().AddSyst(
      cb, 'CMS_zlfake', 'lnN', ch.SystMap('channel','process')
        (['mt'], ['ZL'], 1.5))
  
  cb.cp().AddSyst(
    cb, 'CMS_Wnorm_mt', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['W'],    1.05))
      #(['mm'], ['W'],    1.05))
  
  cb.cp().AddSyst(
    cb, 'CMS_Wnorm_mm', 'lnN', ch.SystMap('channel','process')
      (['mm'], ['W'],    1.05))
      #(['mm'], ['W'],    1.05))
  
  # only for mt channel
  cb.cp().process(['ZJ']).AddSyst(
    cb, 'CMS_zjFakeTau', 'lnN', ch.SystMap('channel')
        (['mt'],          1.1))
  cb.cp().AddSyst(
    cb, 'CMS_qcd_mt', 'lnN', ch.SystMap('channel','process')
        (['mt'], ['QCD'], 1.3))
    
  if doshapes:
    cb.cp().AddSyst( 
      cb, 'shape_tes', 'shape', ch.SystMap('channel','process')
        (['mt'], procs['sig']['mt']+['TTT'], 1.0))
    cb.cp().AddSyst( 
      cb, 'shape_jtf', 'shape', ch.SystMap('channel','process')
        (['mt'], ['ZJ'], 1.0))
    cb.cp().AddSyst( 
      cb, 'shape_jtf', 'shape', ch.SystMap('channel','process')
        (['mt'], ['W'], 1.0))
    cb.cp().AddSyst( 
      cb, 'shape_jtf', 'shape', ch.SystMap('channel','process')
        (['mt'], ['QCD'], 1.0))
    cb.cp().AddSyst( 
      cb, 'shape_jtf', 'shape', ch.SystMap('channel','process')
        (['mt'], ['TTJ'], 1.0))
    #cb.cp().AddSyst( 
    #    cb, 'shape_Zpt', 'shape', ch.SystMap('channel','process')
    #    (['mt'], ['ZTT', 'ZL'], 1.0))
    cb.cp().AddSyst( 
      cb, 'shape_ltf', 'shape', ch.SystMap('channel','process')
        (['mt'], ['ZL', 'TTL'], 1.0))
  
  # EXTRACT SHAPES
  print('>> Extracting histograms from input root files...')
  #file = aux_shapes
  #file = aux_shapes + 'datacard_combine_1p.root'
  for chn in channels:
    cb.cp().channel([chn]).ExtractShapes(
      '%s' % (files[chn]),
      '$BIN/$PROCESS', '$BIN/$PROCESS_$SYSTEMATIC')
  
  # AUTO REBIN
  rebin = ch.AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.1).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(verbosity)
  rebin.Rebin(cb,cb)
  cb.SetAutoMCStats(cb, 0, 1, 1) 
  # STANDARDIZED BIN NAMES
  print(">>> Setting standardised bin names...")
  #ch.SetStandardBinNames(cb)
  ch.SetStandardBinNames(cb,"$CHANNEL") #$CHANNEL_$BIN_$ERA
  if verbosity>=1:
    cb.PrintAll()
  
  # WRITE DATACARDS
  print(">>> Writing datacards...")
  writer = ch.CardWriter(
    "$TAG/$ANALYSIS_%s_$ERA%s.card.txt"%(wp,tag), #$ERA_$MASS
    "$TAG/$ANALYSIS_%s_$ERA%s.input.root"%(wp,tag)
  )
  writer.SetVerbosity(verbosity+1)
  writer.WriteCards(outdir,cb.cp())
    
  print('>> Done!')
  

if __name__ == '__main__':
  description = '''This script makes datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="harvesterDatacards",description=description,epilog="Succes!")
  parser.add_argument('filename_mt',      help="ROOT file with input histograms for mutau channel (SR)")
  #parser.add_argument('filename_mm',      help="ROOT file with input histograms for mumu channel (CR)")
  parser.add_argument('-y', '--era',      default='2018',
                                          help="select era, e.g. 'UL2018'")
  parser.add_argument('-t', '--tag',      default="",
                                          help="tag for the output file names")
  parser.add_argument('-S', '--noshapes', dest='doshapes', action='store_false',
                                          help="include shape variations")
  parser.add_argument('-w', '--wp',       default="",
                                          help="tag for the output file names")
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
  
