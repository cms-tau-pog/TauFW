# Description: Common configuration file for creating pico sample set plotting scripts
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, setera, getyear, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset

def getsampleset(channel,era,**kwargs):
  verbosity = LOG.getverbosity(kwargs)
  year  = getyear(era) # get integer year
  split = kwargs.get('split', ['DY']       ) # split samples (e.g. DY) into genmatch components
  join  = kwargs.get('join',  ['VV','Top'] ) # join samples (e.g. VV, top)
  tag   = kwargs.get('tag',   ""           )
  table = kwargs.get('table', True         ) # print sample set table
  setera(era) # set era for plot style and lumi-xsec normalization
  
  # SM BACKGROUND MC SAMPLES
  if era=='2016':
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
      ( 'WJ', "WJetsToLNu",            "W + jets",           50260.0  ),
      ( 'WJ', "W1JetsToLNu",           "W + 1J",              9625.0  ),
      ( 'WJ', "W2JetsToLNu",           "W + 2J",              3161.0  ),
      ( 'WJ', "W3JetsToLNu",           "W + 3J",               954.8  ),
      ( 'WJ', "W4JetsToLNu",           "W + 4J",               494.6  ),
      ( 'VV', "WW",                    "WW",                    75.88 ),
      ( 'VV', "WZ",                    "WZ",                    27.6  ),
      ( 'VV', "ZZ",                    "ZZ",                    12.14 ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
      ( 'TT', "TT",                    "ttbar",                831.76, {'extraweight': 'ttptweight'} ),
    ]
  elif era=='2017':
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': 'zptweight'} ),
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
  elif era=='UL2017':
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      #( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': 'zptweight'} ),
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
  elif era=='2018':
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': 'zptweight'} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': 'zptweight'} ),
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
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  
  # OBSERVED DATA SAMPLES
  if   'tautau' in channel: dataset = "Tau_Run%d?"%year
  elif 'mutau'  in channel: dataset = "SingleMuon_Run%d?"%year
  elif 'etau'   in channel: dataset = "EGamma_Run%d?"%year if year==2018 else "SingleElectron_Run%d?"%year
  elif 'mumu'   in channel: dataset = "SingleMuon_Run%d?"%year
  elif 'emu'    in channel: dataset = "SingleMuon_Run%d?"%year
  elif 'ee'     in channel: dataset = "EGamma_Run%d?"%year if year==2018 else "SingleElectron_Run%d?"%year
  else:
    LOG.throw(IOError,"Did not recognize channel %r!"%(channel))
  datasample = ('Data',dataset) # GROUP, NAME
  
  # SAMPLE SET
  weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2"
  if era=='UL2017':
    weight = weight.replace("*idweight_2","")
  fname  = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  
  # JOIN
  # Note: titles are set via STYLE.sample_titles
  sampleset.stitch("W*Jets",    incl='WJ',  name='WJ'     ) # W + jets
  sampleset.stitch("DY*J*M-50", incl='DYJ', name="DY_M50" ) # Drell-Yan, M > 50 GeV
  #sampleset.stitch("DY*J*M-10to50", incl='DYJ', name="DY_M10to50" )
  sampleset.join('DY', name='DY'  ) # Drell-Yan, M < 50 GeV + M > 50 GeV
  if 'VV' in join:
    sampleset.join('VV','WZ','WW','ZZ', name='VV'  ) # Diboson
  if 'TT' in join and era!='year':
    sampleset.join('TT', name='TT' ) # ttbar
  if 'ST' in join:
    sampleset.join('ST', name='ST' ) # single top
  if 'Top' in join:
    sampleset.join('TT','ST', name='Top' ) # ttbar + single top
  
  # SPLIT
  # Note: titles are set via STYLE.sample_titles
  if split and channel.count('tau')==1:
    ZTT = STYLE.sample_titles.get('ZTT',"Z -> %s"%channel) # title
    if channel.count('tau')==1:
      ZTT = ZTT.replace("{l}","{mu}" if "mu" in channel else "{e}")
      GMR = "genmatch_2==5"
      GML = "genmatch_2>0 && genmatch_2<5"
      GMJ = "genmatch_2==0"
      GMF = "genmatch_2<5"
    elif channel.count('tau')==2:
      ZTT = ZTT.replace("{l}","{h}")
      GMR = "genmatch_1==5 && genmatch_2==5"
      GML = "(genmatch_1<5 || genmatch_2<5) && genmatch_1>0 && genmatch_2>0"
      GMJ = "(genmatch_1==0 || genmatch_2==0)"
      GMF = "(genmatch_1<5 || genmatch_2<5)"
    else:
      LOG.throw(IOError,"Did not recognize channel %r!"%(channel))
    if 'DY' in split:
      sampleset.split('DY',[('ZTT',ZTT,GMR),('ZL',GML),('ZJ',GMJ),])
    if 'DM' in split: # split DY by decay modes
      samples.split('DY', [('ZTT_DM0', ZTT+", h^{#pm}",                   GMR+" && decayMode_2==0"),
                           ('ZTT_DM1', ZTT+", h^{#pm}h^{0}",              GMR+" && decayMode_2==1"),
                           ('ZTT_DM10',ZTT+", h^{#pm}h^{#mp}h^{#pm}",     GMR+" && decayMode_2==10"),
                           ('ZTT_DM11',ZTT+", h^{#pm}h^{#mp}h^{#pm}h^{0}",GMR+" && decayMode_2==11"),
                           ('ZL',GML),('ZJ',GMJ),])
    if 'TT' in split:
      sampleset.split('TT',[('TTT',GMR),('TTJ',GMF),])
  
  if table:
    sampleset.printtable(merged=True,split=True)
  return sampleset
  
