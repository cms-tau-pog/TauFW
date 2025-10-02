#! /usr/bin/env python
# Author: Yuta Takahashi & Izaak Neutelings (January 2018)
import os #, sys, re
from argparse import ArgumentParser
import CombineHarvester.CombineTools.ch as ch
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True


def main(args):
  
  # SETTINGS
  filename_mt = args.filename_mt # SR
  filename_mm = args.filename_mm # CR
  outdir      = "cards"
  wp          = args.wp
  era         = args.era
  tag         = args.tag
  doshapes    = args.doshapes
  method      = args.method # 'jtf' or 'MC'
  verbosity   = args.verbosity
  if verbosity>=1:
    print ">>> filename_mt = %r"%(filename_mt)
    print ">>> filename_mm = %r"%(filename_mm)
    print ">>> wp          = %r"%(wp)
    print ">>> era         = %r"%(era)
    print ">>> tag         = %r"%(tag)
    print ">>> method      = %r"%(method)
    print ">>> doshapes    = %r"%(doshapes)
  
  # PROCESSES
  procs = {
    'sig': {
      'mt':['ZTT'],
      'mm':['ZLL']
    },
    'bkg': {
      'mt': ['TTT','TTJ','TTL','ZL','ST','VV'],
      'mm': ['TT','W','ST','VV','QCD'],
    }
  }
  if method=='MC': # estimate W with MC
    procs['bkg']['mt'].extend(['ZJ','W','QCD'])
  else: # j -> tau fake rate method
    procs['bkg']['mt'].append('JTF')
  if verbosity>=1:
    print ">>> procs['sig'] = %r"%(procs['sig'])
    print ">>> procs['bkg'] = %r"%(procs['bkg'])
  
  # CATEGORIES
  channels = ['mt', 'mm']
  #channels = ['mt']
  categories = {
    'mt': [(0,wp)],
    'mm': [(1,'ZMM')],
  }
  files = {
    'mt': filename_mt,
    'mm': filename_mm,
  }
  
  # HARVESTER
  cb = ch.CombineHarvester()
  for chn in channels:
    ana  = ['ztt']
    eras = [era]
    cb.AddObservations(['*'],ana,eras,[chn],categories[chn])
    if chn=='mt':
      cb.AddProcesses(['*'], ana,eras,[chn],procs['bkg'][chn],categories[chn], False)
      cb.AddProcesses(['90'],ana,eras,[chn],procs['sig'][chn],categories[chn], True )
    if chn=='mm':
      cb.AddProcesses(['*'], ana,eras,[chn],procs['bkg'][chn],categories[chn], False)
      cb.AddProcesses(['90'],ana,eras,[chn],procs['sig'][chn],categories[chn], False)
  print '>> Add systematics...'
  # template
  #cb.cp().AddSyst(
  #  cb, 'CMS_lumi', 'lnN', ch.SystMap('channel','process')
  #    (['mt'], real_m,                    1.03)
  #    (['em'], ['ZTT', 'TT', 'W', 'VV'],  1.03)
  #    (['mm'], ['ZTT', 'VV', 'ZLL'],      1.06)
  #    (['mm'], ['W'],                     1.03))
  #cb.cp().AddSyst(
  #  cb, 'CMS_lumi_efflep', 'lnN', ch.SystMap('channel','process')
  #    (['mt'], ['TT', 'ST', 'VV','ZJ', 'ZL'] + procs['sig'], 1.04)
  #    (['mm'], procs['bkg']['mm'] + ['ZLL'],             1.05))
  cb.cp().AddSyst(
    cb, 'CMS_lumi', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ'] + procs['sig']['mt'],                    1.025)
      (['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.025))
  cb.cp().AddSyst(
    cb, 'CMS_eff_m', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ']  + procs['sig']['mt'],                    1.02)
      (['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.04))
  cb.cp().AddSyst(
    cb, 'CMS_trig_m', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL', 'ZL', 'ST', 'VV', 'ZJ'] + procs['sig']['mt'],                    1.02)
      (['mm'], ['TT', 'W', 'ST', 'VV'] + ['ZLL'],             1.02))
  cb.cp().AddSyst(
    cb, 'CMS_ttxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['TTT', 'TTJ', 'TTL'],             1.055)
      (['mm'], ['TT'],             1.055))
  cb.cp().AddSyst(
    cb, 'CMS_stxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['ST'],             1.055)
      (['mm'], ['ST'],             1.055))
  cb.cp().AddSyst(
    cb, 'CMS_vvxsec', 'lnN', ch.SystMap('channel','process')
      (['mt'], ['VV'],             1.06)
      (['mm'], ['VV'],             1.06))
  #cb.cp().AddSyst(
  #  cb, 'CMS_dyxsec', 'lnN', ch.SystMap('channel','process')
  #    (['mt'], ['ZTT', 'ZJ', 'ZL'], 1.02)
  #    (['mm'], ['ZLL'],             1.02))
  cb.cp().AddSyst(
    cb, 'CMS_dyxsec', 'rateParam', ch.SystMap('channel','process')
      (['mt'], ['ZTT', 'ZJ', 'ZL'], 1.0)
      (['mm'], ['ZLL'],             1.0))
  
  if era == '2018':
    cb.cp().AddSyst(
      cb, 'CMS_zlfake', 'lnN', ch.SystMap('channel','process')
        (['mt'], ['ZL'], 2.0))
  else:
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
  
  if method=='MC':
    # only for mt channel
    cb.cp().process(['ZJ']).AddSyst(
      cb, 'CMS_zjFakeTau', 'lnN', ch.SystMap('channel')
        (['mt'],          1.1))
    cb.cp().AddSyst(
      cb, 'CMS_qcd_mt', 'lnN', ch.SystMap('channel','process')
        (['mt'], ['QCD'], 1.3))
    #cb.cp().AddSyst(
    #  cb, 'CMS_qcd_mm', 'lnN', ch.SystMap('channel','process')
    #    (['mm'], ['QCD'], 1.3))
  
  elif method=='jtf' and doshapes:
    cb.cp().AddSyst( 
      cb, 'shape_fakeRate', 'shape', ch.SystMap('channel','process')
      (['mt'], ['JTF'], 1.0))
    #cb.cp().process(['JTF']).AddSyst(
    #  cb, 'CMS_$ANALYSIS_qcdSyst_$BIN_$CHANNEL_$ERA', 'lnN', ch.SystMap('channel')
    #    (['mt'],      1.3))  # From Tyler's studies
  
  # mu->tau fakes and QCD norm should be added
  
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
  print '>> Extracting histograms from input root files...'
  #file = aux_shapes
  #file = aux_shapes + 'datacard_combine_1p.root'
  for chn in channels:
    cb.cp().channel([chn]).ExtractShapes(
      '%s' % (files[chn]),
      '$BIN/$PROCESS', '$BIN/$PROCESS_$SYSTEMATIC')
  #cb.cp().backgrounds().ExtractShapes(
  #  file, '$BIN/$PROCESS', '$BIN/$PROCESS_$SYSTEMATIC')
  #cb.cp().signals().ExtractShapes(
  #  file, '$BIN/$PROCESS$MASS', '$BIN/$PROCESS$MASS_$SYSTEMATIC')
  
  # AUTO REBIN
  rebin = ch.AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.1).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(verbosity)
  rebin.Rebin(cb,cb)
  #print '>> Generating bbb uncertainties...'
  #bbb = ch.BinByBinFactory()
  #bbb.SetAddThreshold(0.15).SetFixNorm(False)
  #bbb.AddBinByBin(cb.cp().process(procs['sig'] + procs['bkg']['mt'] + procs['bkg']['mm'] + ['ZLL']), cb)
  
  # STANDARDIZED BIN NAMES
  print ">>> Setting standardised bin names..."
  #ch.SetStandardBinNames(cb)
  ch.SetStandardBinNames(cb,"$CHANNEL") #$CHANNEL_$BIN_$ERA
  if verbosity>=1:
    cb.PrintAll()
  
  # WRITE DATACARDS
  print ">>> Writing datacards..."
  writer = ch.CardWriter(
    "$TAG/$ANALYSIS_%s_$ERA%s.card.txt"%(wp,tag), #$ERA_$MASS
    "$TAG/$ANALYSIS_%s_$ERA%s.input.root"%(wp,tag)
  )
  writer.SetVerbosity(verbosity+1)
  writer.WriteCards(outdir,cb.cp())
  #writer = ch.CardWriter(
  #  "$TAG/$ANALYSIS_$BIN-$ERA%s.txt"%(tag), #$ERA_$MASS
  #  "$TAG/$ANALYSIS_$BIN-$ERA%s.input.root"%(tag)
  #)
  #writer.SetVerbosity(verbosity+1)
  #for chn in channels:  # plus a subdir per channel
  #  print chn
  #  #print 'writing', #chn, cb.cp().channel([chn])
  #  writer.WriteCards(outdir,cb.cp().channel([chn]))
  #writer.SetVerbosity(1)
  #writer.WriteCards('output/sm_cards/LIMITS', cb)
  #writer = ch.CardWriter('$TAG/datacard.txt',
  #                       '$TAG/shapes.root')
  #writer.SetWildcardMasses([])  # We don't use the $MASS property here
  #writer.SetVerbosity(1)
  #x = writer.WriteCards('%s/cmb' % args.output, cb)  # All cards combined
  #print x
  #x['%s/cmb/datacard.txt' % args.output].PrintAll()
  #for chn in channels:  # plus a subdir per channel
  #    writer.WriteCards('%s/%s' % (args.output, chn), cb.cp().channel([chn]))
  
  print '>> Done!'
  

if __name__ == '__main__':
  description = '''This script makes datacards with CombineHarvester.'''
  parser = ArgumentParser(prog="harvesterDatacards",description=description,epilog="Succes!")
  parser.add_argument('filename_mt',      help="ROOT file with input histograms for mutau channel (SR)")
  parser.add_argument('filename_mm',      help="ROOT file with input histograms for mumu channel (CR)")
  parser.add_argument('-y', '--era',      default='2018',
                                          help="select era, e.g. 'UL2018'")
  parser.add_argument('-t', '--tag',      default="",
                                          help="tag for the output file names")
  parser.add_argument('-m', '--method',   choices=['jtf','MC'],default='MC',
                                          help="background estimation method: MC or j -> tau fake rate method")
  parser.add_argument('-S', '--noshapes', dest='doshapes', action='store_false',
                                          help="include shape variations")
  parser.add_argument('-w', '--wp',       default="",
                                          help="tag for the output file names")
  parser.add_argument('-v', '--verbose',  dest='verbosity', type=int, nargs='?', const=1, default=0,
                                          help="set verbosity level" )
  args = parser.parse_args()
  main(args)
  
