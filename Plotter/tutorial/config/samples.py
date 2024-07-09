##Author: Paola Mastrapasqua (Feb 2024)
# Description: Common configuration file for creating pico sample set plotting scripts
import re
from TauFW.Plotter.sample.utils import LOG, STYLE, ensuredir, repkey, joincuts, joinweights, ensurelist,\
                                       setera, getyear, loadmacro, Sel, Var
from TauFW.Plotter.sample.utils import getsampleset as _getsampleset
import json

f = open("../../PicoProducer/samples/nanoaod_sumw_2022_postEE.json")
nevts_json = json.load(f)

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
  #setera(era,cme=13.6) # set era for plot style and lumi-xsec normalization
  if 'TT' in split and 'Top' in join: # don't join TT & ST
    join.remove('Top')
    join += ['TT','ST']
 
  if '2018' in era: # Run2 - UL2018
    kfactor_dy= 3*2025.74/5343.0 # LO->NNLO+NLO_EW k-factor 
    kfactor_wj= 3*20508.9/52940.0
        
    setera(era)
    expsamples = [ # table of MC samples to be converted to Sample objects
      # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
      ( "DY", "DYJetsToLL_M-50",       "Drell-Yan 50",        5343.0*kfactor_dy, {'extraweight': dyweight, 'nevts': 197649078.0} ), # apply k-factor in stitching
      ( 'WJ', "WJetsToLNu",            "W + jets",           52940.0*kfactor_wj, {'nevts': 81051269.0} ),
      ( 'VV', "WW",                    "WW",                    75.88, {'nevts': 15679000.0} ),
      ( 'VV', "WZ",                    "WZ",                    27.6,  {'nevts': 7940000.0}  ),
      ( 'VV', "ZZ",                    "ZZ",                    12.14, {'nevts': 3526000.0} ),
      ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          88.29, {'extraweight': ttweight, 'nevts': 143848848.0}),
      ( 'TT', "TTToHadronic",          "ttbar hadronic",       377.96, {'extraweight': ttweight, 'nevts': 331506194.0}),
      ( 'TT', "TTToSemiLeptonic",      "ttbar semileptonic",   365.35, {'extraweight': ttweight, 'nevts': 472557630.0}),
      ]
  
 
  # SM BACKGROUND MC SAMPLES ##need initial number of events because of the skimming performed in private nanoprod
  elif '2022_postEE' in era: # so far same samples and cross sections are used for preEE and postEE, if event numbers are set elsewhere then we don't need to add seperate numbers for both eras
    # for now nevts is set to 1 so it isn't taken into account in the scaling of the samples as this will be done elsewhere
    
    kfactor_dy=6282.6/5455.0 # LO->NNLO+NLO_EW k-factor computed for 13.6 TeV [https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV]
    kfactor_wj=63425.1/55300 # LO->NNLO+NLO_EW k-factor computed for 13.6 TeV
    kfactor_ttbar=923.6/762.1 # NLO->NNLO k-factor computed for 13.6 TeV
    kfactor_ww=1.524 # LO->NNLO+NLO_EW computed for 13.6 TeV
    kfactor_zz=1.524 # LO->NNLO+NLO_EW computed for 13.6 TeV
    kfactor_wz=1.414 # LO->NNLO+NLO_EW computed for 13.6 TeV 

    setera(era,cme=13.6)
    cme=13.6 
    
    expsamples = [ # table of MC samples to be converted to Sample objects
     # GROUP NAME                     TITLE                 XSEC      EXTRA OPTIONS
     ( 'DY', "DYto2L-4Jets_MLL-50",   "Drell-Yan 50",        5455.0*kfactor_dy, {'extraweight': dyweight , 'nevts':nevts_json["DYto2L-4Jets_MLL-50"]} ), # LO times kfactor
     ( 'WJ', "WtoLNu-4Jets",            "W + jets",           55300.*kfactor_wj, {'nevts':nevts_json["WtoLNu-4Jets"]} ), # LO times kfactor 
     ( 'VV', "WW",             "WW",                    80.23*kfactor_ww, {'nevts':nevts_json["WW"]} ), # LO times kfactor
     ( 'VV', "WZ",             "WZ",                    29.1*kfactor_wz, {'nevts':nevts_json["WZ"]}), # LO times kfactor
     ( 'VV', "ZZ",             "ZZ",                    12.75*kfactor_zz, {'nevts':nevts_json["ZZ"]} ), # LO times kfactor

     ( 'TT', "TTTo2L2Nu",             "ttbar 2l2#nu",          80.9*kfactor_ttbar, {'extraweight': ttweight, 'nevts':nevts_json["TTTo2L2Nu"]} ), # NLO times BR times kfactor
     ( 'TT', "TTto4Q",                "ttbar hadronic",       346.4*kfactor_ttbar, {'extraweight': ttweight, 'nevts': nevts_json["TTto4Q"]} ), # NLO times BR times kfactor
     ( 'TT', "TTtoLNu2Q",             "ttbar semileptonic",   334.8*kfactor_ttbar, {'extraweight': ttweight, 'nevts':nevts_json["TTtoLNu2Q"]} ), # NLO times BR times kfactor
     ]
  else:
    LOG.throw(IOError,"Did not recognize era %r!"%(era))
  
  # OBSERVED DATA SAMPLES
  if   'tautau' in channel: dataset = "Tau_Run%d?"%year
  elif 'mutau'  in channel:
    if era=='2022_preEE':
      dataset = "*Muon_Run%d?"%year
      print("dataset = ", dataset) 
      #dataset = "SingleMuon_Run%d?"%year # need this one as well for C
      # TODO: need to somehow handle that we need SingleMuonC, MuonC, and MuonD for preEE
    elif era=='2022_postEE': dataset = "Muon_Run%d?"%year
    else: dataset = "SingleMuon_Run%d?"%year
  elif 'etau'   in channel: dataset = "EGamma_Run%d?"%year if (year==2018 or year==2022) else "SingleElectron_Run%d?"%year
  elif 'ee'   in channel: dataset = "EGamma_Run%d?"%year if (year==2018 or year==2022) else "SingleElectron_Run%d?"%year
  elif 'mumu'   in channel:
    if era=='2022_preEE':        
      dataset = "Muon_Run%d?"%year
    elif era=='2022_postEE': dataset = "Muon_Run%d?"%year
    else: dataset = "SingleMuon_Run%d?"%year       
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
    weight = "sign(genweight)*trigweight*puweight*idisoweight_1*idweight_2*ltfweight_2"
  elif channel in ['tautau','ditau']:
    weight = "genweight*trigweight*puweight*idweight_1*idweight_2*ltfweight_1*ltfweight_2"
  else: # mumu, emu, ...
    weight = "sign(genweight)*trigweight*puweight*idisoweight_1*idisoweight_2"
  for sf in rmsfs: # remove (old) SFs, e.g. for SF measurement
    weight = weight.replace(sf,"").replace("**","*").strip('*')
  for sf in addsfs:  # add extra SFs, e.g. for SF measurement
    weight = joinweights(weight,sf)
  kwargs.setdefault('weight',weight) # common weight for MC
  kwargs.setdefault('fname', fname)  # default filename pattern
  print(expsamples)
  sampleset = _getsampleset(datasample,expsamples,channel=channel,era=era,**kwargs)
  LOG.verb("weight = %r"%(weight),verbosity,1)
  
  
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
  
