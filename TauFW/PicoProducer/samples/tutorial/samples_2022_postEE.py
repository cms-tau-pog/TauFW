from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE/$DAS"
storage_new = "/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE_new/$DAS"
storage_eraE = "/eos/cms/store/group/phys_tau/irandreo/Run3_22/$DAS"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/2022_postEE/$SAMPLE.txt" 
samples  = [
  
  # DRELL-YAN
  M('DY','DYto2L-4Jets_MLL-50',
    "/DYto2L-4Jets_MLL-50",
    store=storage_new,url=url,files=filelist,opts="useT1=False,zpt=True"),
  
  #W+Jets
  M('WJ','WtoLNu-4Jets',
    "/WtoLNu-4Jets",
    store=storage_new,url=url,files=filelist,opts="useT1=False"),
   
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTto4Q',
    "/TTto4Q",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTtoLNu2Q',
    "/TTtoLNu2Q",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
   
  # DIBOSON
  M('VV','WW',
    "/WW",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZ',
    "/WZ",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZ',
    "/ZZ",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
   
  # SINGLE MUON
  D('Data','Muon_Run2022E',"/Muon_Run2022E",
   store=storage_eraE,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022F',"/Muon_Run2022F",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022G',"/Muon_Run2022G",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
 ]
