from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE/$DAS"
url      = "root://cms-xrd-global.cern.ch/"
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
  
  # SINGLE MUON
  D('Data','Muon_Run2022F',"/Muon_Run2022F",
   store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022G',"/Muon_Run2022G",
   store=storage,url=url,files=filelist,opts="useT1=True",channels=["skim*",'mutau','mumu','emu']),

]
