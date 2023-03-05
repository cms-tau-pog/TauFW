# Description: Common configuration file for creating pico sample set plotting scripts
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, joinweights, ensurelist,\
                                       setera, getyear, loadmacro, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset

def getsampleset(channel,era,**kwargs):
  verbosity = LOG.getverbosity(kwargs)
  year     = getyear(era) # get integer year
  fname    = kwargs.get('fname', "$PICODIR/$SAMPLE_$CHANNEL$TAG.root" ) # file name pattern of pico files
  split    = kwargs.get('split',    ['DY'] if 'tau' in channel else [ ] ) # split samples (e.g. DY) into genmatch components
  join     = kwargs.get('join',     ['VV','Top'] ) # join samples (e.g. VV, top)
  rmsfs    = ensurelist(kwargs.get('rmsf', [ ])) # remove the tau ID SF, e.g. rmsf=['idweight_2','ltfweight_2']
  addsfs   = ensurelist(kwargs.get('addsf', [ ])) # add extra weight to all samples
  weight   = kwargs.get('weight',   None         ) # weight for all MC samples
  dyweight = kwargs.get('dyweight', 'zptweight'  ) # weight for DY samples
  ttweight = kwargs.get('ttweight', 'ttptweight' ) # weight for ttbar samples
  filter   = kwargs.get('filter',   None         ) # only include these MC samples
  vetoes   = kwargs.get('vetoes',   None         ) # veto these MC samples
  #tag      = kwargs.get('tag',      ""           ) # extra tag for sample file names
  table    = kwargs.get('table',    True         ) # print sample set table
  setera(era) # set era for plot style and lumi-xsec normalization
  if 'TT' in split and 'Top' in join: # don't join TT & ST
    join.remove('Top')
    join += ['TT','ST']
  
  # SM BACKGROUND MC SAMPLES
  if 'UL' in era: # UltraLegacy
    
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {"nevts" : 99288125.0}),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight, "nevts":197553995.0} ), # apply k-factor in stitching
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight, "nevts": 60368985.0} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight, "nevts": 27494377.0} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight, "nevts": 20466041.0} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight, "nevts": 8885353.0} ),
      ( 'WJ', "WJetsToLNu",            "W + jets",           52940.0, {"nevts" : 82442496} ),
      ( 'WJ', "W1JetsToLNu",           "W + 1J",              8104.0, {"nevts" : 47903177}  ),
      ( 'WJ', "W2JetsToLNu",           "W + 2J",              2793.0, {"nevts" : 27411802}  ),
      ( 'WJ', "W3JetsToLNu",           "W + 3J",               992.5, {"nevts" : 18297679}  ),
      ( 'WJ', "W4JetsToLNu",           "W + 4J",               544.3, {"nevts" : 9130068}  ),
   
      #( 'VV', "WWTo1L1Nu2Q",           "WW",                    51.65,{"nevts" : 24232603.0} ),
      ( 'VV', "WWTo2L2Nu",             "WW",                    11.09,{"nevts" : 9956710.0} ),
      #( 'VV', "WWTo4Q",                "WW",                    51.03,{"nevts" : 24087772.0} ),
      #( 'VV', "WZTo1L1Nu2Q",           "WZ",                    9.119,{"nevts" : 4262213.0} ),
      ( 'VV', "WZTo2Q2L",              "WZ",                    6.419,{"nevts" : 17820214.0} ),
      ( 'VV', "WZTo3LNu",              "WZ",                    5.213,{"nevts" : 6482815.0} ),
      ( 'VV', "ZZTo2L2Nu",             "ZZ",                   0.6008,{"nevts" : 56766176.0} ),
      ( 'VV', "ZZTo2Q2L",              "ZZ",                    3.676,{"nevts" : 19020772.0} ),
      #( 'VV', "ZZTo2Q2Nu",             "ZZ",                    4.057,{"nevts" : 12544560.0} ),
      ( 'VV', "ZZTo4L",                "ZZ",                    1.325,{"nevts" : 98187568.0} ),
      #( 'VV', "ZZTo4Q",                "ZZ",                    3.262,{"nevts" : 1047365.0} ),

      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': ttweight, "nevts" : 144831008} ),
      ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': ttweight, "nevts" : 340284492.0} ),
      ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': ttweight, "nevts" : 475111154.0} ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02, {"nevts" : 167505220} ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95, {"nevts" : 90216506} ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85, {"nevts" : 11269836} ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85, {"nevts" : 11015416} ),
    ]
    #if 'mutau' in channel:
    #  expsamples.append(('DY',"DYJetsToMuTauh_M-50","DYJetsToMuTauh_M-50",5343.0,{'extraweight': dyweight})) # apply correct normalization in stitching
  elif era=='2016': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        4963.0, {'extraweight': dyweight} ), # apply k-factor in stitching
      ( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",     1012.0, {'extraweight': dyweight} ),
      ( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      334.7, {'extraweight': dyweight} ),
      ( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      102.3, {'extraweight': dyweight} ),
      ( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      54.52, {'extraweight': dyweight} ),
      ( 'WJ', "WJetsToLNu",            "W + jets",           50260.0  ),
      ( 'WJ', "W1JetsToLNu",           "W + 1J",              9625.0  ),
      ( 'WJ', "W2JetsToLNu",           "W + 2J",              3161.0  ),
      ( 'WJ', "W3JetsToLNu",           "W + 3J",               954.8  ),
      ( 'WJ', "W4JetsToLNu",           "W + 4J",               494.6  ),
      ( 'VV', "WW",                    "WW",                    75.88 ),
      ( 'VV', "WZ",                    "WZ",                    27.6  ),
      ( 'VV', "ZZ",                    "ZZ",                    12.14 ),
      ( 'TT', "TT",                    "ttbar",                831.76, {'extraweight': ttweight} ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
    ]
  elif era=='2017': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ), # apply k-factor in stitching
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
      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': ttweight} ),
      ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': ttweight} ),
      ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': ttweight} ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
    ]
  elif era=='UL2017': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      #( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': 'zptweight'} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight} ), # apply k-factor while stitching
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
      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': ttweight} ),
      ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': ttweight} ),
      ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': ttweight} ),
      ( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      ( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      ( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      ( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
    ]
  elif era=='2018': # pre-UL
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      #( 'DY', "DYJetsToLL_M-10to50",   "Drell-Yan 10-50",    18610.0, {'extraweight': dyweight} ),
      ( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0, {'extraweight': dyweight} ), # apply k-factor while stitching
      #( 'DY', "DY1JetsToLL_M-50",      "Drell-Yan 1J 50",      877.8, {'extraweight': dyweight} ),
      #( 'DY', "DY2JetsToLL_M-50",      "Drell-Yan 2J 50",      304.4, {'extraweight': dyweight} ),
      #( 'DY', "DY3JetsToLL_M-50",      "Drell-Yan 3J 50",      111.5, {'extraweight': dyweight} ),
      #( 'DY', "DY4JetsToLL_M-50",      "Drell-Yan 4J 50",      44.05, {'extraweight': dyweight} ),
      #( 'WJ', "WJetsToLNu",            "W + jets",           52940.0  ),
      #( 'WJ', "W1JetsToLNu",           "W + 1J",              8104.0  ),
      #( 'WJ', "W2JetsToLNu",           "W + 2J",              2793.0  ),
      #( 'WJ', "W3JetsToLNu",           "W + 3J",               992.5  ),
      #( 'WJ', "W4JetsToLNu",           "W + 4J",               544.3  ),
      #( 'VV', "WW",                    "WW",                    75.88 ),
      #( 'VV', "WZ",                    "WZ",                    27.6  ),
      #( 'VV', "ZZ",                    "ZZ",                    12.14 ),
      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': ttweight} ),
      #( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': ttweight} ),
      #( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': ttweight} ),
      #( 'ST', "ST_t-channel_top",      "ST t-channel t",       136.02 ),
      #( 'ST', "ST_t-channel_antitop",  "ST t-channel at",       80.95 ),
      #( 'ST', "ST_tW_top",             "ST tW",                 35.85 ),
      #( 'ST', "ST_tW_antitop",         "ST atW",                35.85 ),
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
  
  # FILTER
  if filter:
    expsamples = [s for s in expsamples if any(f in s[0] for f in filter)]
  if vetoes:
    expsamples = [s for s in expsamples if not any(v in s[0] for v in vetoes)]
  
  # SAMPLE SET
  if weight=="":
    weight = ""
  #elif channel in ['mutau','etau']:
  if 'mutau' in channel or 'etau' in channel:
    weight = "genweight/genweight*trigweight*puweight*idisoweight_1*idweight_2*ltfweight_2"
  elif channel in ['tautau','ditau']:
    weight = "genweight*trigweight*puweight*idweight_1*idweight_2*ltfweight_1*ltfweight_2"
  else: # mumu, emu, ...
    weight = "genweight/genweight*trigweight*puweight*idisoweight_1*idisoweight_2"
  for sf in rmsfs: # remove (old) SFs, e.g. for SF measurement
    weight = weight.replace(sf,"").replace("**","*").strip('*')
  for sf in addsfs:  # add extra SFs, e.g. for SF measurement
    weight = joinweights(weight,sf)
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  LOG.verb("weight = %r"%(weight),verbosity,1)
  
  # STITCH
  # Note: titles are set via STYLE.sample_titles
  sampleset.stitch("W*Jets",    incl='WJ',  name='WJ'     ) # W + jets
  sampleset.stitch("DY*J*M-50", incl='DYJ', name="DY_M50" ) # Drell-Yan, M > 50 GeV
  #sampleset.stitch("DY*J*M-10to50", incl='DYJ', name="DY_M10to50" )
  
  # JOIN
  sampleset.join('DY', name='DY' ) # Drell-Yan, M < 50 GeV + M > 50 GeV
  if 'VV' in join:
    sampleset.join('VV','WZ','WW','ZZ', name='VV' ) # Diboson
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
    if 'DM' in split: # split DY by decay modes
      samples.split('DY', [('ZTTDM0', ZTT+", h^{#pm}",                   GMR+" && dm_2==0"),
                           ('ZTTDM1', ZTT+", h^{#pm}h^{0}",              GMR+" && dm_2==1"),
                           ('ZTTDM10',ZTT+", h^{#pm}h^{#mp}h^{#pm}",     GMR+" && dm_2==10"),
                           ('ZTTDM11',ZTT+", h^{#pm}h^{#mp}h^{#pm}h^{0}",GMR+" && dm_2==11"),
                           ('ZL',GML),('ZJ',GMJ),])
    elif 'DY' in split:
      sampleset.split('DY',[('ZTT',ZTT,GMR),('ZL',GML),('ZJ',GMJ),])
    if 'TT' in split:
      sampleset.split('TT',[('TTT',GMR),('TTJ',GMF),])
  
  if table:
    sampleset.printtable(merged=True,split=True)
  print ">>> common weight: %r"%(weight)
  return sampleset
  
