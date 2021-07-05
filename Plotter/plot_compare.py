#! /usr/bin/env python
# Author: Izaak Neutelings (July 2021
# Description: Compare distributions in pico analysis tuples
import os
from config.samples import * # for general getsampleset
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset # for getsampleset_simple
from TauFW.Plotter.plot.Plot import Plot, deletehist
from TauFW.Plotter.plot.Plot import LOG as PLOG
from TauFW.Plotter.sample.utils import MC


def getmcsample(group,sample,title,xsec,channel,era,tag="",verb=0,**kwargs):
  """Simplified version of Plotter/config/samples.py:getsampleset"""
  #LOG.header("getmcsamples")
  fname = kwargs.get('fname', "$PICODIR/$SAMPLE_$CHANNEL$TAG.root" ) # file name pattern of pico files
  if 'e' in channel:
    channel = channel.replace('e','ele')
  fname_ = repkey(fname,USER=user,ERA=era,GROUP=group,SAMPLE=sample,CHANNEL=channel,TAG=tag)
  if not os.path.isfile(fname_):
    print ">>> Did not find %r"%(fname_)
  name   = sample+tag
  if verb>=1:
    print ">>> getmcsample: %s, %s, %s"%(name,sample,fname_)
  sample = MC(name,title,fname_,xsec)
  return sample
  

def getsampleset_simple(channel,era,**kwargs):
  """Simplified version of Plotter/config/samples.py:getsampleset"""
  fname = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  if 'mutau' in channel:
    weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2*ltfweight_2"
  else:
    weight = "genweight*trigweight*puweight*idweight_1*idweight_2*ltfweight_1*ltfweight_2"
  fname  = kwargs.get('fname',  fname  ) or fname # file name pattern of pico files
  weight = kwargs.get('weight', weight )
  tag    = kwargs.get('tag',    ""     )
  table  = kwargs.get('table',  True   ) # print sample set table
  setera(era) # set era for plot style and lumi-xsec normalization
  year  = getyear(era) # get integer year
  if 'UL' in era: # UltraLegacy
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': 'zptweight'} ), # apply k-factor in stitching
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': 'zptweight'} ),
      ( 'WJ', "WJetsToLNu",            "W + jets",           52940.0  ),
      ( 'WJ', "W1JetsToLNu",           "W + 1J",              8104.0  ),
      ( 'WJ', "W2JetsToLNu",           "W + 2J",              2793.0  ),
      ( 'WJ', "W3JetsToLNu",           "W + 3J",               992.5  ),
      ( 'WJ', "W4JetsToLNu",           "W + 4J",               544.3  ),
      ( 'VV', "WW",                    "WW",                    75.88 ),
      ( 'VV', "WZ",                    "WZ",                    27.6  ),
      ( 'VV', "ZZ",                    "ZZ",                    12.14 ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': 'ttptweight'} ),
      ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': 'ttptweight'} ),
      ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': 'ttptweight'} ),
    ]
    #if 'mutau' in channel:
    #  expsamples.append(('DY',"DYJetsToMuTauh_M-50","DYJetsToMuTauh_M-50",5343.0,{'extraweight': dyweight})) # apply correct normalization in stitching
  elif era=='2016': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      ('DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ('DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
      ('DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
      ('DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
      ('WJ', "WJetsToLNu",            "W + jets",           50260.0, ),
      ('WJ', "W1JetsToLNu",           "W + 1 jet",           9625.0  ),
      ('WJ', "W2JetsToLNu",           "W + 2 jets",          3161.0  ),
      ('WJ', "W3JetsToLNu",           "W + 3 jets",           954.8  ),
      ('WJ', "W4JetsToLNu",           "W + 4 jets",           494.6  ),
      ('TT', "TT",                    "ttbar",                831.76, {'extraweight': 'ttptweight'} ),
    ]
  elif era=='2017': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      ('DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ('DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
      ('DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
      ('DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
      ('WJ', "WJetsToLNu",            "W + jets",           50260.0, ),
      ('WJ', "W1JetsToLNu",           "W + 1 jet",           9625.0  ),
      ('WJ', "W2JetsToLNu",           "W + 2 jets",          3161.0  ),
      ('WJ', "W3JetsToLNu",           "W + 3 jets",           954.8  ),
      ('WJ', "W4JetsToLNu",           "W + 4 jets",           494.6  ),
      ('TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': 'ttptweight'} ),
      ('TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': 'ttptweight'} ),
      ('TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': 'ttptweight'} ),
    ]
  elif era=='2018': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      ('DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ('DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
      ('DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
      ('DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
      ('DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
      ('WJ', "WJetsToLNu",            "W + jets",           50260.0, ),
      ('WJ', "W1JetsToLNu",           "W + 1 jet",           9625.0  ),
      ('WJ', "W2JetsToLNu",           "W + 2 jets",          3161.0  ),
      ('WJ', "W3JetsToLNu",           "W + 3 jets",           954.8  ),
      ('WJ', "W4JetsToLNu",           "W + 4 jets",           494.6  ),
      ('TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': 'ttptweight'} ),
      ('TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': 'ttptweight'} ),
      ('TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': 'ttptweight'} ),
    ]
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  datasamples = { # table of data samples (per channel) to be converted to Sample objects
    'mutau':  ('Data', "SingleMuon_Run%s?"%year),
    'etau':   ('Data', "SingleElectron_Run%s?"%year),
    'tautau': ('Data', "Tau_Run%s?"%year),
  }
  
  # SAMPLE SET
  sampleset = _getsampleset(datasamples,expsamples,channel=channel,era=era,weight=weight,file=fname)
  sampleset.stitch("DY*J*M-50", incl='DYJ', name="DY_M50", npart='NUP' )
  sampleset.stitch("W*Jets",    incl='WJ',  name='WJ',     npart='NUP' )
  if era!='2016':
    sampleset.join('TT')
  sampleset.join('DY', name='DY'  )
  sampleset.printtable()
  return sampleset
  

def compare_cuts(sampleset,channel,tag="",outdir="plots"):
  """Compare different selections."""
  LOG.header("compare_eras")
  
  # SELECTIONS & VARIABLES
  if 'tautau' in channel:
    cuts_iso  = "idDeepTau2017v2VSjet_1>=16 && idDeepTau2017v2VSjet_2>=16"
    antilep   = "idDeepTau2017v2VSe_1>=2 && idDeepTau2017v2VSmu_1>=1 && idDeepTau2017v2VSe_2>=2 && idDeepTau2017v2VSmu_2>=1"
    baseline  = "q_1*q_2<0 && idDecayModeNewDMs_1 && idDecayModeNewDMs_2 && %s && %s && !lepton_vetos_noTau && metfilter"%(antilep,cuts_iso)
  else:
    cuts_iso  = "idDeepTau2017v2VSjet_2>=16"
    antilep   = "idDeepTau2017v2VSe_2>=2 && idDeepTau2017v2VSmu_2>=8"
    baseline  = "q_1*q_2<0 && idMedium_1 && pfRelIso04_all_1<0.15 && idDecayModeNewDMs_2 && %s && %s && !lepton_vetos && metfilter"%(antilep,cuts_iso)
  selections  = [
    ('baseline-medium-tight-muon','Baseline, Medium vs. Tight muon ID',
      Sel('Medium', baseline),
      Sel('Tight',  baseline.replace('idMedium_1','idTight_1')),
    ),
    ('0b-medium-tight-muon','0b, Medium vs. Tight muon ID',
      Sel('Medium', baseline+" && pt_1>50 && pt_2>50 && njets50>=1 && m_vis>100 && nbtag50_loose==0"),
      Sel('Tight',  baseline.replace('idMedium_1','idTight_1'+" && pt_1>50 && pt_2>50 && njets50>=1 && m_vis>100 && nbtag50_loose==0")),
    ),
    ('geq1b-medium-tight-muon','geq1b, Medium vs. Tight muon ID',
      Sel('Medium', baseline+" && pt_1>50 && pt_2>50 && njets50>=1 && m_vis>100 && nbtag50_loose>=1"),
      Sel('Tight',  baseline.replace('idMedium_1','idTight_1'+" && pt_1>50 && pt_2>50 && njets50>=1 && m_vis>100 && nbtag50_loose>=1")),
    ),
  ]
  variables = [
    Var('m_vis', 23, 0, 460),
    Var('pt_1',  "Leading tau_h pt",    18, 0, 270),
    Var('pt_2',  "Subleading tau_h pt", 18, 0, 270),
    Var('jpt_1', 18, 0, 270),
    Var('jpt_2', 18, 0, 270),
    Var('met',   20, 0, 300),
    Var('pt_1+pt_2+jpt_1', 30, 0, 600, fname='ST', cut="jpt_1>50"),
  ]
  
  # SAMPLESETS
  sampleset = makesamples(channel,year)
  snames    = ['SingleMuon','TT',] #'DY','WJ']
  
  # PLOT
  outdir   = ensuredir(outdir)
  parallel = True and False
  for sname in snames:
    if 'Tau' and 'tautau' not in channel: continue
    if 'SingleMuon' and 'mutau' not in channel: continue
    LOG.header(sname)
    sample = sampleset.get(sname,unique=True)
    header = samples[0].title
    for setname, settitle, selection1, selection2 in selections:
      hdict = { }
      text  = "%s: %s"%(channel.replace("tau","tau_{h}"),settitle)
      fname = "%s/compareSels_$VAR_%s_%s%s$TAG"%(outdir,sname,setname,tag)
      for sample in samples:
        vars  = [v for v in variables if v.data or not sample.isdata]
        hists = sample.gethist(vars,selection,parallel=parallel)
        for variable, hist in zip(variables,hists):
          hdict.setdefault(variable,[ ]).append(hist)
      #entries = [str(y) for y in eras] # for legend
      for variable, hists in hdict.iteritems():
        for norm in [False,True]:
          #print norm, hists
          ntag = '_norm' if norm else "_lumi"
          plot = Plot(variable,hists,norm=norm)
          plot.draw(ratio=True,lstyle=1)
          plot.drawlegend(header=header,entries=entries)
          plot.drawtext(text)
          plot.saveas(fname,ext=['png'],tag=ntag) #,'pdf'
          plot.close(keep=True)
        deletehist(hists)
  

def compare_eras(eras,samplesets,channel,tag="",**kwargs):
  """Test plotting of SampleSet class for data/MC comparison."""
  LOG.header("compare_eras",pre=">>>")
  if 'mu' in channel:
    snames = ['TT','DY','WJ','SingleMuon']
  else:
    snames = ['TT','DY','WJ','Tau']
  snames   = kwargs.get('samples',  snames  ) # samples to compare
  outdir   = kwargs.get('outdir',   "plots" )
  parallel = kwargs.get('parallel', True    ) #and False
  norms    = kwargs.get('norm',     [True]  )
  entries  = kwargs.get('entries', [str(e) for e in eras] ) # for legend
  exts     = kwargs.get('exts',     ['png'] ) # figure file extensions
  ensuredir(outdir)
  norms    = ensurelist(norms)
  
  # SELECTIONS
  if 'mutau' in channel:
    idiso1   = "iso_1<0.15"
    idiso2   = "idDecayModeNewDMs_2 && idDeepTau2017v2p1VSjet_2>=16 && idDeepTau2017v2p1VSe_2>=2 && idDeepTau2017v2p1VSmu_2>=8"
    baseline = "q_1*q_2<0 && %s && %s && !lepton_vetoes_notau && metfilter"%(idiso1,idiso2)
  else:
    cuts_iso = "idDeepTau2017v2VSjet_1>=16 && idDeepTau2017v2VSjet_2>=16"
    antilep  = "idDeepTau2017v2VSe_1>=2 && idDeepTau2017v2VSmu_1>=1 && idDeepTau2017v2VSe_2>=2 && idDeepTau2017v2VSmu_2>=1"
    baseline = "q_1*q_2<0 && idDecayModeNewDMs_1 && idDecayModeNewDMs_2 && %s && %s && !lepton_vetos_notau && metfilter"%(antilep,cuts_iso)
  selections = [
    Sel('baseline', baseline),
    Sel('baseline, muon pt > 24 GeV', baseline+" && pt_1>24", fname="baseline-ptgt24"),
  ]
  
  # VARIABLES
  variables = [
    Var('m_vis',  23, 0, 460),
    Var('pt_1',   "Leading tau_h pt",    18, 0, 270),
    Var('pt_2',   "Subleading tau_h pt", 18, 0, 270),
    #Var('jpt_1',  18, 0, 270),
    #Var('jpt_2',  18, 0, 270),
    #Var('met',    20, 0, 300),
    Var('rawDeepTau2017v2p1VSe_2',   "rawDeepTau2017v2p1VSe",   30, 0.70, 1, fname="$VAR_zoom",logy=True,pos='L;y=0.85'),
    Var('rawDeepTau2017v2p1VSmu_2',  "rawDeepTau2017v2p1VSmu",  20, 0.80, 1, fname="$VAR_zoom",logy=True,logyrange=4,pos='L;y=0.85'),
    Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 100, 0.0, 1, pos='L;y=0.85',logy=True,ymargin=2.5),
    Var('rawDeepTau2017v2p1VSjet_2', "rawDeepTau2017v2p1VSjet", 20, 0.80, 1, fname="$VAR_zoom",pos='L;y=0.85'),
  ]
  
  # PLOT
  for sname in snames:
    #LOG.header(sname)
    print ">>> %s"%(sname)
    samples = [samplesets[e].get(sname,unique=True) for e in eras]
    header = samples[0].title
    for selection in selections:
      print ">>> %s: %r"%(selection,selection.selection)
      hdict = { }
      text  = "%s: %s"%(channel.replace("tau","tau_{h}"),selection.title)
      fname = "%s/compare_eras_$VAR_%s_%s%s$TAG"%(outdir,sname,selection.filename,tag)
      for sample in samples:
        vars  = [v for v in variables if v.data or not sample.isdata]
        hists = sample.gethist(vars,selection,parallel=parallel)
        for variable, hist in zip(variables,hists):
          hdict.setdefault(variable,[ ]).append(hist)
      for variable, hists in hdict.iteritems():
        for norm in norms:
          ntag = '_norm' if norm else "" #_lumi"
          plot = Plot(variable,hists,norm=norm)
          plot.draw(ratio=True,lstyle=1)
          plot.drawlegend(header=header,entries=entries)
          plot.drawtext(text)
          plot.saveas(fname,ext=['png'],tag=ntag) #,'pdf'
          plot.close(keep=True)
        deletehist(hists)
    print ">>> "
  

def main(args):
  fname    = None #"$PICODIR/$SAMPLE_$CHANNEL.root" # fname pattern
  eras     = ['UL2018']
  channels = ['mutau',] #'tautau'
  tag      = ""
  
  #### COMPARE SELECTIONS
  ###for era in eras:
  ###  for channel in channels:
  ###    #sampleset = getsampleset(channel,era,fname=fname)
  ###    sampleset = getsampleset_simple(channel,era,fname=fname)
  ###    compare_cuts(sampleset,channel,tag="",outdir="plots")
  ###    sampleset.close()
  
  # COMPARE ERAS
  eras = ['UL2016_preVFP','UL2016_postVFP'] # eras to compare
  for channel in channels:
    samplesets = { }
    for era in eras:
      #samplesets[era] = getsampleset(channel,era,fname=fname,weight="")
      samplesets[era] = getsampleset_simple(channel,era,fname=fname,weight="")
    compare_eras(eras,samplesets,channel=channel,tag=tag,outdir="plots")
    for era in eras:
      samplesets[era].close()
  

if __name__ == "__main__":
  import sys
  from argparse import ArgumentParser
  argv = sys.argv
  description = """Simple plotting script to compare distributions in pico analysis tuples"""
  parser = ArgumentParser(prog="plot_compare",description=description,epilog="Good luck!")
  parser.add_argument('-v', '--verbose', dest='verbosity', type=int, nargs='?', const=1, default=0, action='store',
                                         help="set verbosity" )
  args = parser.parse_args()
  LOG.verbosity = args.verbosity
  PLOG.verbosity = args.verbosity
  main(args)
  print "\n>>> Done."
  
