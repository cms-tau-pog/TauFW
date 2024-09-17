# Description: Common configuration file for creating pico sample set plotting scripts
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, joinweights, ensurelist,\
                                       setera, getyear, loadmacro, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset
import json

#f = open("../../PicoProducer/samples/nanoaod_sumw_2022_postEE.json")
#nevts_json = json.load(f)

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
  setera(era,cme=13.6) # set era for plot style and lumi-xsec normalization
  if 'TT' in split and 'Top' in join: # don't join TT & ST
    join.remove('Top')
    join += ['TT','ST']
  
  # SM BACKGROUND MC SAMPLES
  if '2022_preEE' in era or '2022_postEE' in era or '2023'in era: # so far same samples and cross sections are used for preEE and postEE, if event numbers are set elsewhere then we don't need to add seperate numbers for both eras
    # for now nevts is set to 1 so it isn't taken into account in the scaling of the samples as this will be done elsewhere
    
    kfactor_dy=6282.6/5455.0 # LO->NNLO+NLO_EW k-factor computed for 13.6 TeV [https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV]
    kfactor_wj=63425.1/55300 # LO->NNLO+NLO_EW k-factor computed for 13.6 TeV
    kfactor_ttbar=923.6/762.1 # NLO->NNLO k-factor computed for 13.6 TeV
    kfactor_ww=1.524 # LO->NNLO+NLO_EW computed for 13.6 TeV
    kfactor_zz=1.524 # LO->NNLO+NLO_EW computed for 13.6 TeV
    kfactor_wz=1.414 # LO->NNLO+NLO_EW computed for 13.6 TeV 


    cme=13.6

    if '2023'in era:
      expsamples = [ # table of MC samples to be converted to Sample objects
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
        #( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight }),#, "nevts":nevts_json["DYJetsToLL_M-50"]} ), # LO times kfactor, commenting this one out as it is the same as the one below but in principle it should be possible to conbine this sample with the inclusive one below 
        ( 'DY', "DYto2L-4Jets_MLL-50",   "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight } ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_1J",      "Drell-Yan 1J 50",      978.3*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor currently not available
        ( 'DY', "DYto2L-4Jets_MLL-50_2J",      "Drell-Yan 2J 50",      315.1*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_3J",      "Drell-Yan 3J 50",      93.7*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_4J",      "Drell-Yan 4J 50",      45.4*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets",            "W + jets",           55300.*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets_1J",           "W + 1J",              9128.*kfactor_wj), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets_2J",           "W + 2J",              2922.*kfactor_wj  ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets_3J",           "W + 3J",               861.3*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets_4J",           "W + 4J",               415.4*kfactor_wj), # LO times kfactor
   
        ( 'VV', "WW",             "WW",                    80.23*kfactor_ww ), # LO times kfactor
        ( 'VV', "WZ",             "WZ",                    29.1*kfactor_wz), # LO times kfactor
        ( 'VV', "ZZ",             "ZZ",                    12.75*kfactor_zz ), # LO times kfactor

        ( 'TT', "TTto2L2Nu",             "ttbar 2l2#nu",          80.9*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTto4Q",                "ttbar hadronic",       346.4*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTtoLNu2Q",             "ttbar semileptonic",   334.8*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        #( 'ST', "TBbarQ_t-channel",      "ST t-channel t",       123.8), # NLO
        #( 'ST', "TbarBQ_t-channel",      "ST t-channel at",      75.47), # NLO
        ( 'ST', "TWminustoLNu2Q",             "ST tW semileptonic",         15.8 ), # NLO (36.0) times LNu2Q BR
        ( 'ST', "TWminusto2L2Nu",             "ST tW 2l2#nu",               3.8 ), # NLO (36.0) times 2L2Nu BR
        #( 'ST', "TbarWplustoLNu2Q",         "ST atW semileptonic",          15.9 ), # NLO (36.1) times LNu2Q BR
        #( 'ST', "TbarWplusto2L2Nu",         "ST atW 2l2#nu",                3.8 ), # NLO (36.1) times 2L2Nu BR
      ]
    
    if '2022_preEE' in era:
      expsamples = [ # table of MC samples to be converted to Sample objects
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
        #( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight }),#, "nevts":nevts_json["DYJetsToLL_M-50"]} ), # LO times kfactor, commenting this one out as it is the same as the one below but in principle it should be possible to conbine this sample with the inclusive one below 
        ( 'DY', "DYto2L-4Jets_MLL-50",   "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight } ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_1J",      "Drell-Yan 1J 50",      978.3*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor currently not available
        ( 'DY', "DYto2L-4Jets_MLL-50_2J",      "Drell-Yan 2J 50",      315.1*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_3J",      "Drell-Yan 3J 50",      93.7*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_4J",      "Drell-Yan 4J 50",      45.4*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'WJ', "WJetsToLNu-4Jets",            "W + jets",           55300.*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WJetsToLNu-4Jets_1J",           "W + 1J",              9128.*kfactor_wj), # LO times kfactor
        ( 'WJ', "WJetsToLNu-4Jets_2J",           "W + 2J",              2922.*kfactor_wj  ), # LO times kfactor
        ( 'WJ', "WJetsToLNu-4Jets_3J",           "W + 3J",               861.3*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WJetsToLNu-4Jets_4J",           "W + 4J",               415.4*kfactor_wj), # LO times kfactor
   
        ( 'VV', "WW",             "WW",                    80.23*kfactor_ww ), # LO times kfactor
        ( 'VV', "WZ",             "WZ",                    29.1*kfactor_wz), # LO times kfactor
        ( 'VV', "ZZ",             "ZZ",                    12.75*kfactor_zz ), # LO times kfactor

        ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          80.9*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTto4Q",                "ttbar hadronic",       346.4*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTtoLNu2Q",             "ttbar semileptonic",   334.8*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'ST', "TBbarQ_t-channel",      "ST t-channel t",       123.8), # NLO
        ( 'ST', "TbarBQ_t-channel",      "ST t-channel at",      75.47), # NLO
        ( 'ST', "TWminustoLNu2Q",             "ST tW semileptonic",         15.8 ), # NLO (36.0) times LNu2Q BR
        ( 'ST', "TWminusto2L2Nu",             "ST tW 2l2#nu",               3.8 ), # NLO (36.0) times 2L2Nu BR
        ( 'ST', "TbarWplustoLNu2Q",         "ST atW semileptonic",          15.9 ), # NLO (36.1) times LNu2Q BR
        ( 'ST', "TbarWplusto2L2Nu",         "ST atW 2l2#nu",                3.8 ), # NLO (36.1) times 2L2Nu BR
      ]

     # if 'mutau' in channel:
     #   expsamples.append(('DY',"DYto2TautoMuTauh_M-50","Drell-Yan 50 -> tautau -> mu+tauh",5455.0*kfactor_dy,{'extraweight': dyweight})) # LO (using same cross section as inclusive samples), apply correct normalization in stitching
     #   # the cross section for this exact samples is 1885.0 which is ~ 1/3 the total DY->LL cross section (expected since it only selects taus and not electrons and muons)
     #   # the filter efficiency for this sample (due to tau BRs + kinematic cuts on tau decay products) is 2.865e-02 
    if '2022_postEE' in era:
       expsamples = [ # table of MC samples to be converted to Sample objects
        # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
        #( 'DY', "DYJetsToLL_M-50",       "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight }),#, "nevts":nevts_json["DYJetsToLL_M-50"]} ), # LO times kfactor, commenting this one out as it is the same as the one below but in principle it should be possible to conbine this sample with the inclusive one below 
        ( 'DY', "DYto2L-4Jets_MLL-50",   "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight } ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_1J",      "Drell-Yan 1J 50",      978.3*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor currently not available
        ( 'DY', "DYto2L-4Jets_MLL-50_2J",      "Drell-Yan 2J 50",      315.1*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_3J",      "Drell-Yan 3J 50",      93.7*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'DY', "DYto2L-4Jets_MLL-50_4J",      "Drell-Yan 4J 50",      45.4*kfactor_dy, {'extraweight': dyweight} ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets",            "W + jets",           55300.*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WJetstoLNu-4Jets_1J",           "W + 1J",              9128.*kfactor_wj), # LO times kfactor
        ( 'WJ', "WJetstoLNu-4Jets_2J",           "W + 2J",              2922.*kfactor_wj  ), # LO times kfactor
        ( 'WJ', "WJetstoLNu-4Jets_3J",           "W + 3J",               861.3*kfactor_wj ), # LO times kfactor
        ( 'WJ', "WtoLNu-4Jets_4J",           "W + 4J",               415.4*kfactor_wj), # LO times kfactor
   
        ( 'VV', "WW",             "WW",                    80.23*kfactor_ww ), # LO times kfactor
        ( 'VV', "WZ",             "WZ",                    29.1*kfactor_wz), # LO times kfactor
        ( 'VV', "ZZ",             "ZZ",                    12.75*kfactor_zz ), # LO times kfactor

        ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          80.9*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTto4Q",                "ttbar hadronic",       346.4*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'TT', "TTtoLNu2Q",             "ttbar semileptonic",   334.8*kfactor_ttbar, {'extraweight': ttweight} ), # NLO times BR times kfactor
        ( 'ST', "TBbarQ_t-channel",      "ST t-channel t",       123.8), # NLO
        ( 'ST', "TbarBQ_t-channel",      "ST t-channel at",      75.47), # NLO
        ( 'ST', "TWminustoLNu2Q",             "ST tW semileptonic",         15.8 ), # NLO (36.0) times LNu2Q BR
        ( 'ST', "TWminusto2L2Nu",             "ST tW 2l2#nu",               3.8 ), # NLO (36.0) times 2L2Nu BR
        ( 'ST', "TbarWplustoLNu2Q",         "ST atW semileptonic",          15.9 ), # NLO (36.1) times LNu2Q BR
        ( 'ST', "TbarWplusto2L2Nu",         "ST atW 2l2#nu",                3.8 ), # NLO (36.1) times 2L2Nu BR
      ]
     # if 'mutau' in channel:
     #   expsamples.append(('DY',"DYto2TautoMuTauh_M-50","Drell-Yan 50 -> tautau -> mu+tauh",5455.0*kfactor_dy,{'extraweight': dyweight})) # LO (using same cross section as inclusive samples), apply correct normalization in stitching
     #   # the cross section for this exact samples is 1885.0 which is ~ 1/3 the total DY->LL cross section (expected since it only selects taus and not electrons and muons)
     #   # the filter efficiency for this sample (due to tau BRs + kinematic cuts on tau decay products) is 2.865e-02 
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  
  # OBSERVED DATA SAMPLES
  if   'tautau' in channel: dataset = "Tau_Run%d?"%year
  elif 'mutau'  in channel or 'mumu' in channel:
    if era=='2022_preEE':
      dataset = "*Muon_Run%d?"%year
      print("dataset = ", dataset) 
      #dataset = "SingleMuon_Run%d?"%year # need this one as well for C
      # TODO: need to somehow handle that we need SingleMuonC, MuonC, and MuonD for preEE
    elif era=='2022_postEE': dataset = "Muon_Run%d?"%year
    elif '2023' in era: dataset = "Muon*"
    else: dataset = "SingleMuon_Run%d?"%year
    
  elif 'etau' in channel or 'ee' in channel: 
    if (year==2018 or year==2022):
      dataset = "EGamma_Run%d?"%year
    elif '2023' in era: dataset = "EGamma*" 
    else: "SingleElectron_Run%d?"%year

  elif 'emu'    in channel: dataset = "SingleMuon_Run%d?"%year
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
    weight = "genweight*trigweight*puweight*idisoweight_1*idweight_2*ltfweight_2"
  elif channel in ['tautau','ditau']:
    weight = "genweight*trigweight*puweight*idweight_1*idweight_2*ltfweight_1*ltfweight_2"
  else: # mumu, emu, ...
    weight = "genweight*trigweight*puweight*idisoweight_1*idisoweight_2"
  for sf in rmsfs: # remove (old) SFs, e.g. for SF measurement
    weight = weight.replace(sf,"").replace("**","*").strip('*')
  for sf in addsfs:  # add extra SFs, e.g. for SF measurement
    weight = joinweights(weight,sf)
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  print(expsamples)
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  LOG.verb("weight = %r"%(weight),verbosity,1)
  
  # STITCH
  # Note: titles are set via STYLE.sample_titles
  #sampleset.stitch("W*LNu*",    incl='WJ',  name='WJ', cme=cme     ) # W + jets
  #sampleset.stitch("DYto2L-4Jets_MLL-50*", incl='DYJ', name="DY_M50", cme=cme ) # Drell-Yan, M > 50 GeV
  if '2022_postEE' in era or '2023' in era:
      sampleset.stitch("W*LNu*Jets*",    incl='WtoLNu-4Jets',  name='WJ', cme=cme) # W + jets
  elif '2022_preEE' in era:
      sampleset.stitch("W*LNu*Jets*",    incl='WJetsToLNu-4Jets',  name='WJ', cme=cme) # W + jets
  sampleset.stitch("DYto2L-4Jets_MLL-50*", incl='DYto2L-4Jets_MLL-50', name="DY_M50", cme=cme) 

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
      sampleset.split('TT',[('TTT',GMR),('TTJ',GMF),('TTL',"genmatch_2>0 && genmatch_2<5")])
    if 'ST' in split:
      sampleset.split('ST',[('TTT',"genmatch_2==5 && genmatch_2<5"),('STJ',"genmatch_2<5")])
    # if 'TT' in split:
    #   sampleset.split('TT',[('TTT',GMR),('TTJ',GMF),])
  
  if table:
    sampleset.printtable(merged=True,split=True)
  print(">>> common weight: %r"%(weight))
  return sampleset
  
