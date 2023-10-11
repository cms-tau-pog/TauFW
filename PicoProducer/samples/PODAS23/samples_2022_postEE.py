from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE/$DAS"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None 
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  M('DY','DYto2TautoMuTauh_M-50',
    "/DYto2TautoMuTauh_M-50",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  M('TT','TTto4Q',
    "/TTto4Q",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  M('TT','TTtoLNu2Q',
    "/TTtoLNu2Q",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  
  # DIBOSON
  M('VV','WW',
    "/WW",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VV','WZ',
    "/WZ",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VV','ZZ',
    "/ZZ",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  
  #THREE-BOSON
  M('VVV','WWW_4F',
    "/WWW_4F",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VVV','WWZ_4F',
    "/WWZ_4F",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VVV','WZZ',
    "/WZZ",
    store=storage,url=url,files=filelist,opts="useT1=True"),
   M('VVV','ZZZ',
    "/ZZZ",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  
  #
  M('Sig','GluGluHToTauTau_M125_v2',
    "/GluGluHToTauTau_M125_v2",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('Sig','GluGluHToTauTau_M125_v3',
    "/GluGluHToTauTau_M125_v3",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('Sig','VBFHToTauTau_M125_v2_Poisson70KeepRAW',
    "/VBFHToTauTau_M125_v2_Poisson70KeepRAW",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('Sig','VBFHToTauTau_M125_Poisson60KeepRAW',
    "/VBFHToTauTau_M125_Poisson60KeepRAW",
    store=storage,url=url,files=filelist,opts="useT1=True"),

  # SINGLE MUON
  D('Data','MuonEG_Run2022F',"/MuonEG_Run2022F",
   store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),
  D('Data','MuonEG_Run2022G',"/MuonEG_Run2022G",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022F',"/Muon_Run2022F",
   store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022G',"/Muon_Run2022G",
   store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),
 
  # TAU
  D('Data','Tau_Run2022F',"/Tau_Run2022F",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'tautau']),
  D('Data','Tau_Run2022G',"/Tau_Run2022G",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'tautau']),
  
  # EGamma
  D('Data','EGamma_Run2022F',"/EGamma_Run2022F",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*"]),
  D('Data','EGamma_Run2022G',"/EGamma_Run2022G",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*"]),
  
   # JetMet
  D('Data','JetMet_Run2022F',"/JetMet_Run2022F",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*"]),
  D('Data','JetMet_Run2022G',"/JetMet_Run2022G",
    store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*"]),
  

]
