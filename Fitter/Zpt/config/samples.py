# Description: Common configuration file for creating pico sample set plotting scripts
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, setera, getyear, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset

def getsampleset(channel,era,**kwargs):
  verbosity = LOG.getverbosity(kwargs)
  year     = getyear(era) # get integer year
  dysample = kwargs.get('dy',       "jet"        )
  dyweight = kwargs.get('dyweight', ""           )
  split    = kwargs.get('split',    [ ]          ) # split samples (e.g. DY) into genmatch components
  join     = kwargs.get('join',     ['VV','Top'] ) # join samples (e.g. VV, top)
  tag      = kwargs.get('tag',      ""           )
  table    = kwargs.get('table',    True         ) # print sample set table
  setera(era) # set global era for plot style and lumi-xsec normalization
  
  if 'UL2016' in era and 'VFP' not in era: # join pre-/post-VFP into full UL2016
    kwargs['table'] = False
    kwargs1 = kwargs.copy() # prevent overwriting
    kwargs2 = kwargs.copy() # prevent overwriting
    sampleset1 = getsampleset(channel,era+"_preVFP",**kwargs1)
    sampleset2 = getsampleset(channel,era+"_postVFP",**kwargs2)
    setera(era) # reset era for plot style and lumi-xsec normalization
    sampleset = sampleset1 + sampleset2 # merge samples
    if table:
      sampleset.printtable(merged=True,split=True)
    return sampleset
  
  # SM BACKGROUND MC SAMPLES
  xsec_dy_lo   = 4963.0    # MadGraph (LO)
  xsec_dy_nlo  = 6529.0    # aMC@NLO
  xsec_dy_nnlo = 3*2025.74 # FEWZ (NNLO)
  k_lo         = xsec_dy_nnlo/xsec_dy_lo
  k_nlo        = 1. #xsec_dy_nnlo/xsec_dy_nlo
  if 'UL' in era:
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      #( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0  ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight} ),
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight} ),
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
    if era=='2016':
      expsamples = [ ] # table of MC samples to be converted to Sample objects
      if 'mass' in dysample:
        expsamples += [
          # GROUP NAME                       TITLE                   XSEC             EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-100to200",   "Drell-Yan 100to200",   k_nlo*226.6,       {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-200to400",   "Drell-Yan 200to400",   k_nlo*  7.77,      {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-400to500",   "Drell-Yan 400to500",   k_nlo*  0.4065,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-500to700",   "Drell-Yan 500to700",   k_nlo*  0.2334,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-700to800",   "Drell-Yan 700to800",   k_nlo*  0.03614,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-800to1000",  "Drell-Yan 800to1000",  k_nlo*  0.03047,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1000to1500", "Drell-Yan 1000to1500", k_nlo*  0.01636,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1500to2000", "Drell-Yan 1500to2000", k_nlo*  0.00218,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-2000to3000", "Drell-Yan 2000to3000", k_nlo*  0.0005156, {'extraweight': dyweight} ),
        ]
      else:
        expsamples += [
          # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': dyweight} ),
          ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': dyweight} ),
          ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': dyweight} ),
          ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': dyweight} ),
          ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': dyweight} ),
        ]
      expsamples += [
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
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
      expsamples = [ ] # table of MC samples to be converted to Sample objects
      if 'mass' in dysample:
        expsamples += [
          # GROUP NAME                       TITLE                   XSEC             EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-100to200",   "Drell-Yan 100to200",   k_nlo*247.8,       {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-200to400",   "Drell-Yan 200to400",   k_nlo*  8.502,     {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-400to500",   "Drell-Yan 400to500",   k_nlo*  0.4514,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-500to700",   "Drell-Yan 500to700",   k_nlo*  0.2558,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-700to800",   "Drell-Yan 700to800",   k_nlo*  0.04023,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-800to1000",  "Drell-Yan 800to1000",  k_nlo*  0.03406,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1000to1500", "Drell-Yan 1000to1500", k_nlo*  0.01828,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1500to2000", "Drell-Yan 1500to2000", k_nlo*  0.002367,  {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-2000to3000", "Drell-Yan 2000to3000", k_nlo*  0.0005409, {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-3000toInf",  "Drell-Yan 3000toInf",  k_nlo*  3.048e-05, {'extraweight': dyweight} ),
        ]
      else:
        expsamples += [
          # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight} ),
          ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight} ),
          ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight} ),
          ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight} ),
          ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight} ),
        ]
      expsamples += [
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
        ( 'WJ', "WJetsToLNu",            "W + jets",           52940.0  ),
        ( 'WJ', "W1JetsToLNu",           "W + 1J",              8104.0  ),
        ( 'WJ', "W2JetsToLNu",           "W + 2J",              2793.0  ),
        #( 'WJ', "W3JetsToLNu",           "W + 3J",               992.5  ),
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
      expsamples = [ ] # table of MC samples to be converted to Sample objects
      if 'mass' in dysample:
        expsamples += [
          # GROUP NAME                       TITLE                   XSEC             EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-100to200",   "Drell-Yan 100to200",   k_nlo*247.8,       {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-200to400",   "Drell-Yan 200to400",   k_nlo*  8.502,     {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-400to500",   "Drell-Yan 400to500",   k_nlo*  0.4514,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-500to700",   "Drell-Yan 500to700",   k_nlo*  0.2558,    {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-700to800",   "Drell-Yan 700to800",   k_nlo*  0.04023,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-800to1000",  "Drell-Yan 800to1000",  k_nlo*  0.03406,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1000to1500", "Drell-Yan 1000to1500", k_nlo*  0.01828,   {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-1500to2000", "Drell-Yan 1500to2000", k_nlo*  0.002367,  {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-2000to3000", "Drell-Yan 2000to3000", k_nlo*  0.0005409, {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-3000toInf",  "Drell-Yan 3000toInf",  k_nlo*  3.048e-05, {'extraweight': dyweight} ),
        ]
      else:
        expsamples += [
          # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
          ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ),
          ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight} ),
          ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight} ),
          ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight} ),
          ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight} ),
          ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight} ),
        ]
      expsamples += [
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
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
  dataset = "SingleMuon_Run%d?"%year
  datasample = ('Data',dataset) # GROUP, NAME
  
  # SAMPLE SET
  weight = "genweight*trigweight*puweight*idisoweight_1*idisoweight_2"
  fname  = "$PICODIR/$SAMPLE_$CHANNEL$TAG.root"
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  
  # JOIN
  ZMM = STYLE.sample_titles.get('ZMM',"Z -> mumu") # title
  # Note: titles are set via STYLE.sample_titles
  sampleset.stitch("W*Jets",    incl='WJ',  name='WJ'  ) # W + jets
  if 'mass' not in dysample:
    sampleset.stitch("DY*J*M-10to50", incl='DYJ', name="DY_M10to50" )
    sampleset.stitch("DY*J*M-50", incl='DYJ', name='DY' ) # Drell-Yan, M > 50 GeV
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
  GMR = "genmatch_1>0 && genmatch_2>0"
  GMF = "(genmatch_1<=0 || genmatch_2<=0)"
  if 'DY' in split:
    sampleset.split('DY',[('ZMM',ZMM,GMR),('ZJ',GMF),])
  if 'TT' in split:
    sampleset.split('TT',[('TMM',GMR),('TTJ',GMF),])
  
  if table:
    sampleset.printtable(merged=True,split=True)
  return sampleset
  
