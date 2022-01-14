#! /usr/bin/env python
# Author: Izaak Neutelings (August 2020)
# Description: Create input histograms for datacards
#   ./createinputs.py -c mutau -y UL2017
import sys
from collections import OrderedDict
sys.path.append("../Plotter/") # for config.samples
from config.samples import *
from TauFW.Plotter.plot.utils import LOG as PLOG
from TauFW.Fitter.plot.datacard import createinputs, plotinputs


def main(args):
  channels  = args.channels
  eras      = args.eras
  parallel  = args.parallel
  verbosity = args.verbosity
  plot      = False
  outdir    = ensuredir("input")
  plotdir   = ensuredir(outdir,"plots")
  analysis  = 'ztt' # $PROCESS_$ANALYSIS
  tag       = "13TeV_mtlt50"
  
  for era in eras:
    for channel in channels:
      
      
      ###############
      #   SAMPLES   #
      ###############
      # sample set and their systematic variations
      
      # GET SAMPLESET
      join      = ['VV','TT','ST']
      sname     = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
#      sampleset = getsampleset(channel,era,fname=sname,join=join,split=None,table=False)
      sampleset = getsampleset(channel,era,fname=sname,join=join,split=[],table=False)
      
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
        
        # SPLIT & RENAME (HTT convention)
        GMR = "genmatch_2==5"
        GML = "genmatch_2>0 && genmatch_2<5"
        GMJ = "genmatch_2==0"
        GMF = "genmatch_2<5"
        sampleset.split('DY',[('ZTT',GMR),('ZL',GML),('ZJ',GMJ),])
        sampleset.split('TT',[('TTT',GMR),('TTL',GML),('TTJ',GMJ)])
        #sampleset.split('ST',[('STT',GMR),('STJ',GMF),]) # small background
        sampleset.rename('WJ','W')
        sampleset.datasample.name = 'data_obs'
        
        # SYSTEMATIC VARIATIONS
        varprocs = OrderedDict([ # processes to be varied
          ('Nom',      ['ZTT','ZL','ZJ','W','VV','ST','TTT','TTL','TTJ','QCD','data_obs']), #,'STT','STJ'
          ('TES0.970', ['ZTT']),
          ('TES0.972', ['ZTT']),
          ('TES0.974', ['ZTT']),
          ('TES0.976', ['ZTT']),
          ('TES0.978', ['ZTT']),
          ('TES0.980', ['ZTT']),
          ('TES0.982', ['ZTT']),
          ('TES0.984', ['ZTT']),
          ('TES0.986', ['ZTT']),
          ('TES0.988', ['ZTT']),
          ('TES0.990', ['ZTT']),
          ('TES0.992', ['ZTT']),
          ('TES0.994', ['ZTT']),
          ('TES0.996', ['ZTT']),
          ('TES0.998', ['ZTT']),
          ('TES1.000', ['ZTT']),
          ('TES1.002', ['ZTT']),
          ('TES1.004', ['ZTT']),
          ('TES1.006', ['ZTT']),
          ('TES1.008', ['ZTT']),
          ('TES1.010', ['ZTT']),
          ('TES1.012', ['ZTT']),
          ('TES1.014', ['ZTT']),
          ('TES1.016', ['ZTT']),
          ('TES1.018', ['ZTT']),
          ('TES1.020', ['ZTT']),
          ('TES1.022', ['ZTT']),
          ('TES1.024', ['ZTT']),
          ('TES1.026', ['ZTT']),
          ('TES1.028', ['ZTT']),
          ('TES1.030', ['ZTT']),
          ('LTFUp',   ['ZL', 'TTL']),
          ('LTFDown', ['ZL', 'TTL']),
          ('JTFUp',   ['ZJ', 'TTJ', 'W']),
          ('JTFDown', ['ZJ', 'TTJ', 'W']),
          ('shape_tidUp',     ['ZTT', 'TTT']),
          ('shape_tidDown',     ['ZTT', 'TTT']),
          ('shape_mTauFakeUp',     ['ZL', 'TTL']),
          ('shape_mTauFakeDown',     ['ZL', 'TTL']),
          ('shape_dyUp',     ['ZTT', 'ZL', 'ZJ']),
          ('shape_dyDown',     ['ZTT', 'ZL', 'ZJ']),
        ])
        samplesets = { # sets of samples per variation
          'Nom':     sampleset, # nominal
          'TES0.970':   sampleset.shift(varprocs['TES0.970'],  "_TES0p970","_TES0.970",  " -3.0% TES", split=True,filter=False,share=True),
          'TES0.972':   sampleset.shift(varprocs['TES0.972'],  "_TES0p972","_TES0.972",  " -2.8% TES", split=True,filter=False,share=True),
          'TES0.974':   sampleset.shift(varprocs['TES0.974'],  "_TES0p974","_TES0.974",  " -2.6% TES", split=True,filter=False,share=True),
          'TES0.976':   sampleset.shift(varprocs['TES0.976'],  "_TES0p976","_TES0.976",  " -2.4% TES", split=True,filter=False,share=True),
          'TES0.978':   sampleset.shift(varprocs['TES0.978'],  "_TES0p978","_TES0.978",  " -2.2% TES", split=True,filter=False,share=True),
          'TES0.980':   sampleset.shift(varprocs['TES0.980'],  "_TES0p980","_TES0.980",  " -2.0% TES", split=True,filter=False,share=True),
          'TES0.982':   sampleset.shift(varprocs['TES0.982'],  "_TES0p982","_TES0.982",  " -1.8% TES", split=True,filter=False,share=True),
          'TES0.984':   sampleset.shift(varprocs['TES0.984'],  "_TES0p984","_TES0.984",  " -1.6% TES", split=True,filter=False,share=True),
          'TES0.986':   sampleset.shift(varprocs['TES0.986'],  "_TES0p986","_TES0.986",  " -1.4% TES", split=True,filter=False,share=True),
          'TES0.988':   sampleset.shift(varprocs['TES0.988'],  "_TES0p988","_TES0.988",  " -1.2% TES", split=True,filter=False,share=True),
          'TES0.990':   sampleset.shift(varprocs['TES0.990'],  "_TES0p990","_TES0.990",  " -1.0% TES", split=True,filter=False,share=True),
          'TES0.992':   sampleset.shift(varprocs['TES0.992'],  "_TES0p992","_TES0.992",  " -0.8% TES", split=True,filter=False,share=True),
          'TES0.994':   sampleset.shift(varprocs['TES0.994'],  "_TES0p994","_TES0.994",  " -0.6% TES", split=True,filter=False,share=True),
          'TES0.996':   sampleset.shift(varprocs['TES0.996'],  "_TES0p996","_TES0.996",  " -0.4% TES", split=True,filter=False,share=True),
          'TES0.998':   sampleset.shift(varprocs['TES0.998'],  "_TES0p998","_TES0.998",  " -0.2% TES", split=True,filter=False,share=True),
          'TES1.000':   sampleset.shift(varprocs['TES1.000'],  "_TES1p000","_TES1.000",  " +0.0% TES", split=True,filter=False,share=True),
          'TES1.002':   sampleset.shift(varprocs['TES1.002'],  "_TES1p002","_TES1.002",  " +0.2% TES", split=True,filter=False,share=True),
          'TES1.004':   sampleset.shift(varprocs['TES1.004'],  "_TES1p004","_TES1.004",  " +0.4% TES", split=True,filter=False,share=True),
          'TES1.006':   sampleset.shift(varprocs['TES1.006'],  "_TES1p006","_TES1.006",  " +0.6% TES", split=True,filter=False,share=True),
          'TES1.008':   sampleset.shift(varprocs['TES1.008'],  "_TES1p008","_TES1.008",  " +0.8% TES", split=True,filter=False,share=True),
          'TES1.010':   sampleset.shift(varprocs['TES1.010'],  "_TES1p010","_TES1.010",  " +1.0% TES", split=True,filter=False,share=True),
          'TES1.012':   sampleset.shift(varprocs['TES1.012'],  "_TES1p012","_TES1.012",  " +1.2% TES", split=True,filter=False,share=True),
          'TES1.014':   sampleset.shift(varprocs['TES1.014'],  "_TES1p014","_TES1.014",  " +1.4% TES", split=True,filter=False,share=True),
          'TES1.016':   sampleset.shift(varprocs['TES1.016'],  "_TES1p016","_TES1.016",  " +1.6% TES", split=True,filter=False,share=True),
          'TES1.018':   sampleset.shift(varprocs['TES1.018'],  "_TES1p018","_TES1.018",  " +1.8% TES", split=True,filter=False,share=True),
          'TES1.020':   sampleset.shift(varprocs['TES1.020'],  "_TES1p020","_TES1.020",  " +2.0% TES", split=True,filter=False,share=True),
          'TES1.022':   sampleset.shift(varprocs['TES1.022'],  "_TES1p022","_TES1.022",  " +2.2% TES", split=True,filter=False,share=True),
          'TES1.024':   sampleset.shift(varprocs['TES1.024'],  "_TES1p024","_TES1.024",  " +2.4% TES", split=True,filter=False,share=True),
          'TES1.026':   sampleset.shift(varprocs['TES1.026'],  "_TES1p026","_TES1.026",  " +2.6% TES", split=True,filter=False,share=True),
          'TES1.028':   sampleset.shift(varprocs['TES1.028'],  "_TES1p028","_TES1.028",  " +2.8% TES", split=True,filter=False,share=True),
          'TES1.030':   sampleset.shift(varprocs['TES1.030'],  "_TES1p030","_TES1.030",  " +3.0% TES", split=True,filter=False,share=True),
          'LTFUp':   sampleset.shift(varprocs['LTFUp'],  "_LTFUp","_shape_mTauFake_$BINUp",  " +2% LTF shape", split=True,filter=False,share=True),
          'LTFDown': sampleset.shift(varprocs['LTFDown'],"_LTFDown","_shape_mTauFake_$BINDown"," -2% LTF shape", split=True,filter=False,share=True),
          'JTFUp':   sampleset.shift(varprocs['JTFUp'],  "_JTFUp","_shape_jTauFake_$BINUp",  " +5% JTF",split=True,filter=False,share=True),
          'JTFDown': sampleset.shift(varprocs['JTFDown'],"_JTFDown","_shape_jTauFake_$BINDown"," -5% JTF",split=True,filter=False,share=True),
#          'shape_tidUp':       sampleset.shift(varprocs['shape_tidUp'],"","_shape_tidUp",  " TID shape syst UP", split=True,filter=False,share=True),
#          'shape_tidDown':     sampleset.shift(varprocs['shape_tidDown'],"","_shape_tidDown",  " TID shape syst DOWN", split=True,filter=False,share=True),
#          'shape_mTauFakeUp':  sampleset.shift(varprocs['shape_mTauFakeUp'],"","_shape_mTauFakeSFUp",  " LTF rate syst UP", split=True,filter=False,share=True),
#          'shape_mTauFakeDown':sampleset.shift(varprocs['shape_mTauFakeDown'],"","_shape_mTauFakeSFDown",  " LTF rate syst DOWN", split=True,filter=False,share=True),
#          'shape_dyUp':        sampleset.shift(varprocs['shape_dyUp'],"","_shape_dyUp",  " +10% Zptweight", split=True,filter=False,share=True),
#          'shape_dyDown':      sampleset.shift(varprocs['shape_dyDown'],"","_shape_dyDown",  " -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.970shape_tidUp':   sampleset.shift(varprocs['TES0.970'],  "_TES0p970","_TES0.970_shape_tidUp",  " -3.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.972shape_tidUp':   sampleset.shift(varprocs['TES0.972'],  "_TES0p972","_TES0.972_shape_tidUp",  " -2.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.974shape_tidUp':   sampleset.shift(varprocs['TES0.974'],  "_TES0p974","_TES0.974_shape_tidUp",  " -2.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.976shape_tidUp':   sampleset.shift(varprocs['TES0.976'],  "_TES0p976","_TES0.976_shape_tidUp",  " -2.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.978shape_tidUp':   sampleset.shift(varprocs['TES0.978'],  "_TES0p978","_TES0.978_shape_tidUp",  " -2.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.980shape_tidUp':   sampleset.shift(varprocs['TES0.980'],  "_TES0p980","_TES0.980_shape_tidUp",  " -2.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.982shape_tidUp':   sampleset.shift(varprocs['TES0.982'],  "_TES0p982","_TES0.982_shape_tidUp",  " -1.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.984shape_tidUp':   sampleset.shift(varprocs['TES0.984'],  "_TES0p984","_TES0.984_shape_tidUp",  " -1.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.986shape_tidUp':   sampleset.shift(varprocs['TES0.986'],  "_TES0p986","_TES0.986_shape_tidUp",  " -1.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.988shape_tidUp':   sampleset.shift(varprocs['TES0.988'],  "_TES0p988","_TES0.988_shape_tidUp",  " -1.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.990shape_tidUp':   sampleset.shift(varprocs['TES0.990'],  "_TES0p990","_TES0.990_shape_tidUp",  " -1.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.992shape_tidUp':   sampleset.shift(varprocs['TES0.992'],  "_TES0p992","_TES0.992_shape_tidUp",  " -0.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.994shape_tidUp':   sampleset.shift(varprocs['TES0.994'],  "_TES0p994","_TES0.994_shape_tidUp",  " -0.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.996shape_tidUp':   sampleset.shift(varprocs['TES0.996'],  "_TES0p996","_TES0.996_shape_tidUp",  " -0.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.998shape_tidUp':   sampleset.shift(varprocs['TES0.998'],  "_TES0p998","_TES0.998_shape_tidUp",  " -0.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.000shape_tidUp':   sampleset.shift(varprocs['TES1.000'],  "_TES1p000","_TES1.000_shape_tidUp",  " +0.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.002shape_tidUp':   sampleset.shift(varprocs['TES1.002'],  "_TES1p002","_TES1.002_shape_tidUp",  " +0.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.004shape_tidUp':   sampleset.shift(varprocs['TES1.004'],  "_TES1p004","_TES1.004_shape_tidUp",  " +0.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.006shape_tidUp':   sampleset.shift(varprocs['TES1.006'],  "_TES1p006","_TES1.006_shape_tidUp",  " +0.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.008shape_tidUp':   sampleset.shift(varprocs['TES1.008'],  "_TES1p008","_TES1.008_shape_tidUp",  " +0.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.010shape_tidUp':   sampleset.shift(varprocs['TES1.010'],  "_TES1p010","_TES1.010_shape_tidUp",  " +1.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.012shape_tidUp':   sampleset.shift(varprocs['TES1.012'],  "_TES1p012","_TES1.012_shape_tidUp",  " +1.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.014shape_tidUp':   sampleset.shift(varprocs['TES1.014'],  "_TES1p014","_TES1.014_shape_tidUp",  " +1.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.016shape_tidUp':   sampleset.shift(varprocs['TES1.016'],  "_TES1p016","_TES1.016_shape_tidUp",  " +1.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.018shape_tidUp':   sampleset.shift(varprocs['TES1.018'],  "_TES1p018","_TES1.018_shape_tidUp",  " +1.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.020shape_tidUp':   sampleset.shift(varprocs['TES1.020'],  "_TES1p020","_TES1.020_shape_tidUp",  " +2.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.022shape_tidUp':   sampleset.shift(varprocs['TES1.022'],  "_TES1p022","_TES1.022_shape_tidUp",  " +2.2% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.024shape_tidUp':   sampleset.shift(varprocs['TES1.024'],  "_TES1p024","_TES1.024_shape_tidUp",  " +2.4% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.026shape_tidUp':   sampleset.shift(varprocs['TES1.026'],  "_TES1p026","_TES1.026_shape_tidUp",  " +2.6% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.028shape_tidUp':   sampleset.shift(varprocs['TES1.028'],  "_TES1p028","_TES1.028_shape_tidUp",  " +2.8% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES1.030shape_tidUp':   sampleset.shift(varprocs['TES1.030'],  "_TES1p030","_TES1.030_shape_tidUp",  " +3.0% TES, TID shape syst UP", split=True,filter=False,share=True),
#          'TES0.970shape_tidDown':   sampleset.shift(varprocs['TES0.970'],  "_TES0p970","_TES0.970_shape_tidDown",  " -3.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.972shape_tidDown':   sampleset.shift(varprocs['TES0.972'],  "_TES0p972","_TES0.972_shape_tidDown",  " -2.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.974shape_tidDown':   sampleset.shift(varprocs['TES0.974'],  "_TES0p974","_TES0.974_shape_tidDown",  " -2.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.976shape_tidDown':   sampleset.shift(varprocs['TES0.976'],  "_TES0p976","_TES0.976_shape_tidDown",  " -2.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.978shape_tidDown':   sampleset.shift(varprocs['TES0.978'],  "_TES0p978","_TES0.978_shape_tidDown",  " -2.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.980shape_tidDown':   sampleset.shift(varprocs['TES0.980'],  "_TES0p980","_TES0.980_shape_tidDown",  " -2.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.982shape_tidDown':   sampleset.shift(varprocs['TES0.982'],  "_TES0p982","_TES0.982_shape_tidDown",  " -1.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.984shape_tidDown':   sampleset.shift(varprocs['TES0.984'],  "_TES0p984","_TES0.984_shape_tidDown",  " -1.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.986shape_tidDown':   sampleset.shift(varprocs['TES0.986'],  "_TES0p986","_TES0.986_shape_tidDown",  " -1.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.988shape_tidDown':   sampleset.shift(varprocs['TES0.988'],  "_TES0p988","_TES0.988_shape_tidDown",  " -1.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.990shape_tidDown':   sampleset.shift(varprocs['TES0.990'],  "_TES0p990","_TES0.990_shape_tidDown",  " -1.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.992shape_tidDown':   sampleset.shift(varprocs['TES0.992'],  "_TES0p992","_TES0.992_shape_tidDown",  " -0.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.994shape_tidDown':   sampleset.shift(varprocs['TES0.994'],  "_TES0p994","_TES0.994_shape_tidDown",  " -0.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.996shape_tidDown':   sampleset.shift(varprocs['TES0.996'],  "_TES0p996","_TES0.996_shape_tidDown",  " -0.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.998shape_tidDown':   sampleset.shift(varprocs['TES0.998'],  "_TES0p998","_TES0.998_shape_tidDown",  " -0.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.000shape_tidDown':   sampleset.shift(varprocs['TES1.000'],  "_TES1p000","_TES1.000_shape_tidDown",  " +0.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.002shape_tidDown':   sampleset.shift(varprocs['TES1.002'],  "_TES1p002","_TES1.002_shape_tidDown",  " +0.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.004shape_tidDown':   sampleset.shift(varprocs['TES1.004'],  "_TES1p004","_TES1.004_shape_tidDown",  " +0.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.006shape_tidDown':   sampleset.shift(varprocs['TES1.006'],  "_TES1p006","_TES1.006_shape_tidDown",  " +0.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.008shape_tidDown':   sampleset.shift(varprocs['TES1.008'],  "_TES1p008","_TES1.008_shape_tidDown",  " +0.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.010shape_tidDown':   sampleset.shift(varprocs['TES1.010'],  "_TES1p010","_TES1.010_shape_tidDown",  " +1.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.012shape_tidDown':   sampleset.shift(varprocs['TES1.012'],  "_TES1p012","_TES1.012_shape_tidDown",  " +1.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.014shape_tidDown':   sampleset.shift(varprocs['TES1.014'],  "_TES1p014","_TES1.014_shape_tidDown",  " +1.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.016shape_tidDown':   sampleset.shift(varprocs['TES1.016'],  "_TES1p016","_TES1.016_shape_tidDown",  " +1.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.018shape_tidDown':   sampleset.shift(varprocs['TES1.018'],  "_TES1p018","_TES1.018_shape_tidDown",  " +1.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.020shape_tidDown':   sampleset.shift(varprocs['TES1.020'],  "_TES1p020","_TES1.020_shape_tidDown",  " +2.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.022shape_tidDown':   sampleset.shift(varprocs['TES1.022'],  "_TES1p022","_TES1.022_shape_tidDown",  " +2.2% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.024shape_tidDown':   sampleset.shift(varprocs['TES1.024'],  "_TES1p024","_TES1.024_shape_tidDown",  " +2.4% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.026shape_tidDown':   sampleset.shift(varprocs['TES1.026'],  "_TES1p026","_TES1.026_shape_tidDown",  " +2.6% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.028shape_tidDown':   sampleset.shift(varprocs['TES1.028'],  "_TES1p028","_TES1.028_shape_tidDown",  " +2.8% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES1.030shape_tidDown':   sampleset.shift(varprocs['TES1.030'],  "_TES1p030","_TES1.030_shape_tidDown",  " +3.0% TES, TID shape syst DOWN", split=True,filter=False,share=True),
#          'TES0.970shape_dyUp':   sampleset.shift(varprocs['TES0.970'],  "_TES0p970","_TES0.970_shape_dyUp",  " -3.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.972shape_dyUp':   sampleset.shift(varprocs['TES0.972'],  "_TES0p972","_TES0.972_shape_dyUp",  " -2.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.974shape_dyUp':   sampleset.shift(varprocs['TES0.974'],  "_TES0p974","_TES0.974_shape_dyUp",  " -2.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.976shape_dyUp':   sampleset.shift(varprocs['TES0.976'],  "_TES0p976","_TES0.976_shape_dyUp",  " -2.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.978shape_dyUp':   sampleset.shift(varprocs['TES0.978'],  "_TES0p978","_TES0.978_shape_dyUp",  " -2.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.980shape_dyUp':   sampleset.shift(varprocs['TES0.980'],  "_TES0p980","_TES0.980_shape_dyUp",  " -2.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.982shape_dyUp':   sampleset.shift(varprocs['TES0.982'],  "_TES0p982","_TES0.982_shape_dyUp",  " -1.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.984shape_dyUp':   sampleset.shift(varprocs['TES0.984'],  "_TES0p984","_TES0.984_shape_dyUp",  " -1.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.986shape_dyUp':   sampleset.shift(varprocs['TES0.986'],  "_TES0p986","_TES0.986_shape_dyUp",  " -1.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.988shape_dyUp':   sampleset.shift(varprocs['TES0.988'],  "_TES0p988","_TES0.988_shape_dyUp",  " -1.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.990shape_dyUp':   sampleset.shift(varprocs['TES0.990'],  "_TES0p990","_TES0.990_shape_dyUp",  " -1.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.992shape_dyUp':   sampleset.shift(varprocs['TES0.992'],  "_TES0p992","_TES0.992_shape_dyUp",  " -0.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.994shape_dyUp':   sampleset.shift(varprocs['TES0.994'],  "_TES0p994","_TES0.994_shape_dyUp",  " -0.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.996shape_dyUp':   sampleset.shift(varprocs['TES0.996'],  "_TES0p996","_TES0.996_shape_dyUp",  " -0.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.998shape_dyUp':   sampleset.shift(varprocs['TES0.998'],  "_TES0p998","_TES0.998_shape_dyUp",  " -0.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.000shape_dyUp':   sampleset.shift(varprocs['TES1.000'],  "_TES1p000","_TES1.000_shape_dyUp",  " +0.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.002shape_dyUp':   sampleset.shift(varprocs['TES1.002'],  "_TES1p002","_TES1.002_shape_dyUp",  " +0.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.004shape_dyUp':   sampleset.shift(varprocs['TES1.004'],  "_TES1p004","_TES1.004_shape_dyUp",  " +0.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.006shape_dyUp':   sampleset.shift(varprocs['TES1.006'],  "_TES1p006","_TES1.006_shape_dyUp",  " +0.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.008shape_dyUp':   sampleset.shift(varprocs['TES1.008'],  "_TES1p008","_TES1.008_shape_dyUp",  " +0.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.010shape_dyUp':   sampleset.shift(varprocs['TES1.010'],  "_TES1p010","_TES1.010_shape_dyUp",  " +1.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.012shape_dyUp':   sampleset.shift(varprocs['TES1.012'],  "_TES1p012","_TES1.012_shape_dyUp",  " +1.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.014shape_dyUp':   sampleset.shift(varprocs['TES1.014'],  "_TES1p014","_TES1.014_shape_dyUp",  " +1.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.016shape_dyUp':   sampleset.shift(varprocs['TES1.016'],  "_TES1p016","_TES1.016_shape_dyUp",  " +1.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.018shape_dyUp':   sampleset.shift(varprocs['TES1.018'],  "_TES1p018","_TES1.018_shape_dyUp",  " +1.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.020shape_dyUp':   sampleset.shift(varprocs['TES1.020'],  "_TES1p020","_TES1.020_shape_dyUp",  " +2.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.022shape_dyUp':   sampleset.shift(varprocs['TES1.022'],  "_TES1p022","_TES1.022_shape_dyUp",  " +2.2% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.024shape_dyUp':   sampleset.shift(varprocs['TES1.024'],  "_TES1p024","_TES1.024_shape_dyUp",  " +2.4% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.026shape_dyUp':   sampleset.shift(varprocs['TES1.026'],  "_TES1p026","_TES1.026_shape_dyUp",  " +2.6% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.028shape_dyUp':   sampleset.shift(varprocs['TES1.028'],  "_TES1p028","_TES1.028_shape_dyUp",  " +2.8% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES1.030shape_dyUp':   sampleset.shift(varprocs['TES1.030'],  "_TES1p030","_TES1.030_shape_dyUp",  " +3.0% TES, +10% Zptweight", split=True,filter=False,share=True),
#          'TES0.970shape_dyDown':   sampleset.shift(varprocs['TES0.970'],  "_TES0p970","_TES0.970_shape_dyDown",  " -3.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.972shape_dyDown':   sampleset.shift(varprocs['TES0.972'],  "_TES0p972","_TES0.972_shape_dyDown",  " -2.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.974shape_dyDown':   sampleset.shift(varprocs['TES0.974'],  "_TES0p974","_TES0.974_shape_dyDown",  " -2.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.976shape_dyDown':   sampleset.shift(varprocs['TES0.976'],  "_TES0p976","_TES0.976_shape_dyDown",  " -2.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.978shape_dyDown':   sampleset.shift(varprocs['TES0.978'],  "_TES0p978","_TES0.978_shape_dyDown",  " -2.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.980shape_dyDown':   sampleset.shift(varprocs['TES0.980'],  "_TES0p980","_TES0.980_shape_dyDown",  " -2.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.982shape_dyDown':   sampleset.shift(varprocs['TES0.982'],  "_TES0p982","_TES0.982_shape_dyDown",  " -1.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.984shape_dyDown':   sampleset.shift(varprocs['TES0.984'],  "_TES0p984","_TES0.984_shape_dyDown",  " -1.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.986shape_dyDown':   sampleset.shift(varprocs['TES0.986'],  "_TES0p986","_TES0.986_shape_dyDown",  " -1.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.988shape_dyDown':   sampleset.shift(varprocs['TES0.988'],  "_TES0p988","_TES0.988_shape_dyDown",  " -1.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.990shape_dyDown':   sampleset.shift(varprocs['TES0.990'],  "_TES0p990","_TES0.990_shape_dyDown",  " -1.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.992shape_dyDown':   sampleset.shift(varprocs['TES0.992'],  "_TES0p992","_TES0.992_shape_dyDown",  " -0.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.994shape_dyDown':   sampleset.shift(varprocs['TES0.994'],  "_TES0p994","_TES0.994_shape_dyDown",  " -0.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.996shape_dyDown':   sampleset.shift(varprocs['TES0.996'],  "_TES0p996","_TES0.996_shape_dyDown",  " -0.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES0.998shape_dyDown':   sampleset.shift(varprocs['TES0.998'],  "_TES0p998","_TES0.998_shape_dyDown",  " -0.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.000shape_dyDown':   sampleset.shift(varprocs['TES1.000'],  "_TES1p000","_TES1.000_shape_dyDown",  " +0.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.002shape_dyDown':   sampleset.shift(varprocs['TES1.002'],  "_TES1p002","_TES1.002_shape_dyDown",  " +0.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.004shape_dyDown':   sampleset.shift(varprocs['TES1.004'],  "_TES1p004","_TES1.004_shape_dyDown",  " +0.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.006shape_dyDown':   sampleset.shift(varprocs['TES1.006'],  "_TES1p006","_TES1.006_shape_dyDown",  " +0.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.008shape_dyDown':   sampleset.shift(varprocs['TES1.008'],  "_TES1p008","_TES1.008_shape_dyDown",  " +0.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.010shape_dyDown':   sampleset.shift(varprocs['TES1.010'],  "_TES1p010","_TES1.010_shape_dyDown",  " +1.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.012shape_dyDown':   sampleset.shift(varprocs['TES1.012'],  "_TES1p012","_TES1.012_shape_dyDown",  " +1.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.014shape_dyDown':   sampleset.shift(varprocs['TES1.014'],  "_TES1p014","_TES1.014_shape_dyDown",  " +1.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.016shape_dyDown':   sampleset.shift(varprocs['TES1.016'],  "_TES1p016","_TES1.016_shape_dyDown",  " +1.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.018shape_dyDown':   sampleset.shift(varprocs['TES1.018'],  "_TES1p018","_TES1.018_shape_dyDown",  " +1.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.020shape_dyDown':   sampleset.shift(varprocs['TES1.020'],  "_TES1p020","_TES1.020_shape_dyDown",  " +2.0% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.022shape_dyDown':   sampleset.shift(varprocs['TES1.022'],  "_TES1p022","_TES1.022_shape_dyDown",  " +2.2% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.024shape_dyDown':   sampleset.shift(varprocs['TES1.024'],  "_TES1p024","_TES1.024_shape_dyDown",  " +2.4% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.026shape_dyDown':   sampleset.shift(varprocs['TES1.026'],  "_TES1p026","_TES1.026_shape_dyDown",  " +2.6% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.028shape_dyDown':   sampleset.shift(varprocs['TES1.028'],  "_TES1p028","_TES1.028_shape_dyDown",  " +2.8% TES, -10% Zptweight", split=True,filter=False,share=True),
#          'TES1.030shape_dyDown':   sampleset.shift(varprocs['TES1.030'],  "_TES1p030","_TES1.030_shape_dyDown",  " +3.0% TES, -10% Zptweight", split=True,filter=False,share=True),
        }
        keys = samplesets.keys() if verbosity>=1 else ['Nom','TES1.030','TES0.970','TES1.020','TES0.980','TES1.010','TES0.990']
        for shift in keys:
          if not shift in samplesets: continue
          samplesets[shift].printtable(merged=True,split=True)
          if verbosity>=2:
            samplesets[shift].printobjs(file=True)
      
      
      ###################
      #   OBSERVABLES   #
      ###################
      # observable/variables to be fitted in combine
      
      restriction = {
        'dm_2==1(?!0)(?!1)': '0.35<m_2 && m_2<1.20', # [ 0.3, 1.3*sqrt(pt/100) ]
        'dm_2==10':          '0.83<m_2 && m_2<1.43', # [ 0.8, 1.5 ] -> +-3%: [ 0.824, 1.455 ], +-2%: [ 0.816, 1.470 ]
        'dm_2==11':          '0.93<m_2 && m_2<1.53', # [ 0.9, 1.6 ] -> +-3%: [ 0.927, 1.552 ], +-2%: [ 0.918, 1.568 ]
      }

      if channel=='mumu':
      
        observables = [
          Var('m_vis', 1, 60, 120, ymargin=1.6, rrange=0.08),
        ]
      
      else:
        
        #mvis = Var('m_vis', 10, 36, 106)
        observables = [
          Var('m_vis',              8,   50,  106, tag='',       cut="50<m_vis && m_vis<106" ),
          Var('m_2',   "m_tau_h",  13,  0.3,  1.6, tag='',       cut="0.3<m_2 && m_2<1.6", ccut=restriction, veto="dm_2==0"),
          #Var('m_2',     36, 0.23, 2.03, tag='_0p05',  cut="0.3<m_2 && m_2<2.0", ccut=restriction, veto="dm_2==0"),
          #Var('m_vis',  8, 50, 106),
		  #Var('m_2',   "m_tau_h",     26,  0.3, 1.6),
          #Var('m_vis', 15, 50, 200, tag="_10"), # coarser binning
        ]
        
        # PT & DM BINS
        # drawing observables can be run in parallel
        # => use 'cut' option as hack to save time drawing pt or DM bins
        #    instead of looping over many selection,
        #    also, each pt/DM bin will be a separate file
        #dmbins = [0,1,10,11]
        #ptbins = [20,25,30,35,40,50,70,2000] #500,1000]
        #print ">>> DM cuts:"
        #for dm in dmbins:
        #  dmcut = "dm_2==%d"%(dm)
        #  fname = "$VAR_dm%s"%(dm)
        #  mvis_cut = mvis.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
        #  m2_cut   = m2.clone(fname=fname,cut=dmcut) # create observable with extra cut for dm bin
        #  print ">>>   %r (%r)"%(dmcut,fname)
        #  observables.append(mvis_cut)
        #  observables.append(m2_cut)
        #print ">>> pt cuts:"
        #for imax, ptmin in enumerate(ptbins,1):
        #  if imax<len(ptbins):
        #    ptmax = ptbins[imax]
        #    ptcut = "pt_2>%s && pt_2<=%s"%(ptmin,ptmax)
        #    fname = "$VAR_pt%sto%s"%(ptmin,ptmax)
        #  else: # overflow
        #    #ptcut = "pt_2>%s"%(ptmin)
        #    #fname = "$VAR_ptgt%s"%(ptmin)
        #    continue # skip overflow bin
        #  mvis_cut = mvis.clone(fname=fname,cut=ptcut) # create observable with extra cut for pt bin
        #  print ">>>   %r (%r)"%(ptcut,fname)
        #  observables.append(mvis_cut)
      
      
      ############
      #   BINS   #
      ############
      # selection categories
      
      if channel=='mumu':
        
        baseline  = "q_1*q_2<0 && iso_1<0.15 && iso_2<0.15 && !lepton_vetoes && metfilter"
        bins = [
          Sel('ZMM', baseline),
        ]
      
      else:
        
        baseline  = "(q_1*q_2<0) && iso_1<0.15 && idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=32 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8 && !lepton_vetoes_notau && metfilter"
        signal_region = "%s && mt_1<50"%(baseline)
        signal_regionDM0 = "%s && dm_2==0"%(signal_region)
        signal_regionDM1 = "%s && dm_2==1"%(signal_region)
        signal_regionDM10 = "%s && dm_2==10"%(signal_region)
        signal_regionDM11 = "%s && dm_2==11"%(signal_region)
        bins = [
          #Sel('baseline',          baseline),
          Sel('signal_region',     signal_region),
          Sel('DM0',      signal_regionDM0),
          Sel('DM1',      signal_regionDM1),
          Sel('DM10',     signal_regionDM10),
          Sel('DM11',     signal_regionDM11),
        ]
      
      
      #######################
      #   DATACARD INPUTS   #
      #######################
      # histogram inputs for the datacards
      
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/SMTauTau2016
      chshort = channel.replace('tau','t').replace('mu','m') # abbreviation of channel
      #fname   = "%s/%s_$OBS_%s-%s$TAG%s.inputs.root"%(outdir,analysis,chshort,era,tag)
      fname   = "%s/%s_%s_tes_$OBS.inputs-%s-%s.root"%(outdir,analysis,chshort,era,tag)
      if channel in ['mutau']:
        createinputs(fname,samplesets['Nom'],    observables,bins,recreate=True)
        createinputs(fname,samplesets['TES0.970'],  observables,bins,filter=varprocs['TES0.970'],dots=True)
        createinputs(fname,samplesets['TES0.972'],  observables,bins,filter=varprocs['TES0.972'],dots=True)
        createinputs(fname,samplesets['TES0.974'],  observables,bins,filter=varprocs['TES0.974'],dots=True)
        createinputs(fname,samplesets['TES0.976'],  observables,bins,filter=varprocs['TES0.976'],dots=True)
        createinputs(fname,samplesets['TES0.978'],  observables,bins,filter=varprocs['TES0.978'],dots=True)
        createinputs(fname,samplesets['TES0.980'],  observables,bins,filter=varprocs['TES0.980'],dots=True)
        createinputs(fname,samplesets['TES0.982'],  observables,bins,filter=varprocs['TES0.982'],dots=True)
        createinputs(fname,samplesets['TES0.984'],  observables,bins,filter=varprocs['TES0.984'],dots=True)
        createinputs(fname,samplesets['TES0.986'],  observables,bins,filter=varprocs['TES0.986'],dots=True)
        createinputs(fname,samplesets['TES0.988'],  observables,bins,filter=varprocs['TES0.988'],dots=True)
        createinputs(fname,samplesets['TES0.990'],  observables,bins,filter=varprocs['TES0.990'],dots=True)
        createinputs(fname,samplesets['TES0.992'],  observables,bins,filter=varprocs['TES0.992'],dots=True)
        createinputs(fname,samplesets['TES0.994'],  observables,bins,filter=varprocs['TES0.994'],dots=True)
        createinputs(fname,samplesets['TES0.996'],  observables,bins,filter=varprocs['TES0.996'],dots=True)
        createinputs(fname,samplesets['TES0.998'],  observables,bins,filter=varprocs['TES0.998'],dots=True)
        createinputs(fname,samplesets['TES1.000'],  observables,bins,filter=varprocs['TES1.000'],dots=True  )
        createinputs(fname,samplesets['TES1.002'],  observables,bins,filter=varprocs['TES1.002'],dots=True  )
        createinputs(fname,samplesets['TES1.004'],  observables,bins,filter=varprocs['TES1.004'],dots=True  )
        createinputs(fname,samplesets['TES1.006'],  observables,bins,filter=varprocs['TES1.006'],dots=True  )
        createinputs(fname,samplesets['TES1.008'],  observables,bins,filter=varprocs['TES1.008'],dots=True  )
        createinputs(fname,samplesets['TES1.010'],  observables,bins,filter=varprocs['TES1.010'],dots=True  )
        createinputs(fname,samplesets['TES1.012'],  observables,bins,filter=varprocs['TES1.012'],dots=True  )
        createinputs(fname,samplesets['TES1.014'],  observables,bins,filter=varprocs['TES1.014'],dots=True  )
        createinputs(fname,samplesets['TES1.016'],  observables,bins,filter=varprocs['TES1.016'],dots=True  )
        createinputs(fname,samplesets['TES1.018'],  observables,bins,filter=varprocs['TES1.018'],dots=True  )
        createinputs(fname,samplesets['TES1.020'],  observables,bins,filter=varprocs['TES1.020'],dots=True  )
        createinputs(fname,samplesets['TES1.022'],  observables,bins,filter=varprocs['TES1.022'],dots=True  )
        createinputs(fname,samplesets['TES1.024'],  observables,bins,filter=varprocs['TES1.024'],dots=True  )
        createinputs(fname,samplesets['TES1.026'],  observables,bins,filter=varprocs['TES1.026'],dots=True  )
        createinputs(fname,samplesets['TES1.028'],  observables,bins,filter=varprocs['TES1.028'],dots=True  )
        createinputs(fname,samplesets['TES1.030'],  observables,bins,filter=varprocs['TES1.030'],dots=True  )
        createinputs(fname,samplesets['LTFUp'],  observables,bins,filter=varprocs['LTFUp']  )
        createinputs(fname,samplesets['LTFDown'],observables,bins,filter=varprocs['LTFDown'])
        createinputs(fname,samplesets['JTFUp'],  observables,bins,filter=varprocs['JTFUp']) #,  htag='_JTFUp'  )
        createinputs(fname,samplesets['JTFDown'],observables,bins,filter=varprocs['JTFDown']) #,htag='_JTFDown')
#        createinputs(fname,samplesets['shape_mTauFakeUp'],   observables,bins,                          filter=varprocs['shape_mTauFakeUp'],replaceweight=["ltfweight_2","ltfweightUp_2"]  )
#        createinputs(fname,samplesets['shape_mTauFakeDown'], observables,bins,                          filter=varprocs['shape_mTauFakeDown'],replaceweight=["ltfweight_2","ltfweightDown_2"]  )
#        createinputs(fname,samplesets['shape_tidUp'],        observables,bins,htag="shape_tidUp",       filter=varprocs['shape_tidUp'],replaceweight=["idweight_2","idweightUp_2"]  )
#        createinputs(fname,samplesets['TES0.970shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.970'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.972shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.972'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.974shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.974'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.976shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.976'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.978shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.978'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.980shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.980'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.982shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.982'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.984shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.984'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.986shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.986'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.988shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.988'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.990shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.990'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.992shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.992'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.994shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.994'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.996shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.996'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES0.998shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES0.998'],replaceweight=["idweight_2","idweightUp_2"],dots=True)
#        createinputs(fname,samplesets['TES1.000shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.000'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.002shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.002'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.004shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.004'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.006shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.006'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.008shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.008'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.010shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.010'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.012shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.012'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.014shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.014'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.016shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.016'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.018shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.018'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.020shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.020'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.022shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.022'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.024shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.024'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.026shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.026'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.028shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.028'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['TES1.030shape_tidUp'],  observables,bins,htag="shape_tidUp",       filter=varprocs['TES1.030'],replaceweight=["idweight_2","idweightUp_2"],dots=True  )
#        createinputs(fname,samplesets['shape_tidDown'],      observables,bins,htag="shape_tidDown",     filter=varprocs['shape_tidDown'],replaceweight=["idweight_2","idweightDown_2"]  )
#        createinputs(fname,samplesets['TES0.970shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.970'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.972shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.972'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.974shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.974'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.976shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.976'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.978shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.978'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.980shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.980'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.982shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.982'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.984shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.984'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.986shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.986'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.988shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.988'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.990shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.990'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.992shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.992'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.994shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.994'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.996shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.996'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES0.998shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES0.998'],replaceweight=["idweight_2","idweightDown_2"],dots=True )
#        createinputs(fname,samplesets['TES1.000shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.000'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.002shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.002'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.004shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.004'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.006shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.006'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.008shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.008'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.010shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.010'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.012shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.012'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.014shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.014'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.016shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.016'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.018shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.018'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.020shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.020'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.022shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.022'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.024shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.024'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.026shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.026'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.028shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.028'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['TES1.030shape_tidDown'],  observables,bins,htag="shape_tidDown",     filter=varprocs['TES1.030'],replaceweight=["idweight_2","idweightDown_2"],dots=True   )
#        createinputs(fname,samplesets['shape_dyUp'],         observables,bins,htag="shape_dyUp",        filter=varprocs['shape_dyUp'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"]  )
#        createinputs(fname,samplesets['TES0.970shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.970'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.972shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.972'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.974shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.974'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.976shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.976'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.978shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.978'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.980shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.980'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.982shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.982'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.984shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.984'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.986shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.986'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.988shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.988'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.990shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.990'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.992shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.992'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.994shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.994'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.996shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.996'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.998shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES0.998'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES1.000shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.000'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.002shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.002'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.004shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.004'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.006shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.006'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.008shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.008'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.010shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.010'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.012shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.012'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.014shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.014'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.016shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.016'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.018shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.018'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.020shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.020'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.022shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.022'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.024shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.024'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.026shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.026'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.028shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.028'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.030shape_dyUp'],  observables,bins,htag="shape_dyUp",        filter=varprocs['TES1.030'],replaceweight=["zptweight","(zptweight+0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['shape_dyDown'],       observables,bins,htag="shape_dyDown",      filter=varprocs['shape_dyDown'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"]  )
#        createinputs(fname,samplesets['TES0.970shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.970'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.972shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.972'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.974shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.974'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.976shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.976'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.978shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.978'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.980shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.980'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.982shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.982'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.984shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.984'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.986shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.986'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.988shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.988'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.990shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.990'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.992shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.992'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.994shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.994'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.996shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.996'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES0.998shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES0.998'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True  )
#        createinputs(fname,samplesets['TES1.000shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.000'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.002shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.002'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.004shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.004'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.006shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.006'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.008shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.008'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.010shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.010'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.012shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.012'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.014shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.014'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.016shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.016'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.018shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.018'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.020shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.020'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.022shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.022'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.024shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.024'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.026shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.026'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.028shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.028'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
#        createinputs(fname,samplesets['TES1.030shape_dyDown'],  observables,bins,htag="shape_dyDown",      filter=varprocs['TES1.030'],replaceweight=["zptweight","(zptweight-0.1*(zptweight-1))"],dots=True    )
      
      
      ############
      #   PLOT   #
      ############
      # control plots of the histogram inputs
      
      if plot:
        pname  = "%s/%s_$OBS_%s-$BIN-%s$TAG%s.png"%(plotdir,analysis,chshort,era,tag)
        text   = "%s: $BIN"%(channel.replace("mu","#mu").replace("tau","#tau_{h}"))
        groups = [ ] #(['^TT','ST'],'Top'),]
        plotinputs(fname,varprocs,observables,bins,text=text,
                   pname=pname,tag=tag,group=groups)
      

if __name__ == "__main__":
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Create input histograms for datacards"""
  parser = ArgumentParser(prog="createInputs",description=description,epilog="Good luck!")
  parser.add_argument('-y', '--era',     dest='eras', nargs='*', choices=['2016','2017','2018','UL2016_preVFP','UL2016_postVFP','UL2017','UL2018'], default=['UL2017'], action='store',
                                         help="set era" )
  parser.add_argument('-c', '--channel', dest='channels', nargs='*', choices=['mutau','mumu'], default=['mutau'], action='store',
                                         help="set channel" )
  parser.add_argument('-s', '--serial',  dest='parallel', action='store_false',
                                         help="run Tree::MultiDraw serial instead of in parallel" )
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
