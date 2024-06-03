
from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage = "/eos/cms/store/group/phys_tau/irandreo/Run3_22/$DAS"
url      = "root://cms-xrd-global.cern.ch/"
filelist = None 
samples  = [
  # DRELL-YAN
  #M('DY','DYJetsToLL_M-50',
  #  "/DYJetsToLL_M-50",
  #  store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50',
    "/DYto2L-4Jets_MLL-50",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_1J',
    "/DYto2L-4Jets_MLL-50_1J",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_2J',
    "/DYto2L-4Jets_MLL-50_2J",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_3J',
    "/DYto2L-4Jets_MLL-50_3J",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_4J',
    "/DYto2L-4Jets_MLL-50_4J",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYto2TautoMuTauh_M-50',
    "/DYto2TautoMuTauh_M-50",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),

  #W+Jets
  M('WJ','WJetsToLNu-4Jets',
    "/WJetsToLNu-4Jets",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('WJ','WJetsToLNu-4Jets_1J',
    "/WJetsToLNu-4Jets_1J",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('WJ','WJetsToLNu-4Jets_2J',
    "/WJetsToLNu-4Jets_2J",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('WJ','WJetsToLNu-4Jets_3J',
    "WJetsToLNu-4Jets_3J",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('WJ','WJetsToLNu-4Jets_4J',
    "/WJetsToLNu-4Jets_4J",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
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
  
  # ST
  M('ST','TBbarQ_t-channel',
    "/TBbarQ_t-channel",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TbarBQ_t-channel',
    "/TbarBQ_t-channel",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TWminustoLNu2Q',
    "/TWminustoLNu2Q",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TWminusto2L2Nu',
    "/TWminusto2L2Nu",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TbarWplustoLNu2Q',
    "/TbarWplustoLNu2Q",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TbarWplusto2L2Nu',
    "/TbarWplusto2L2Nu",
    store=storage,url=url,files=filelist,opts="useT1=False"),

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
  
  #THREE-BOSON
  M('VVV','WWW_4F',
    "/WWW_4F",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VVV','WWZ_4F',
    "/WWZ_4F",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VVV','WZZ',
    "/WZZ",
    store=storage,url=url,files=filelist,opts="useT1=False"),
   M('VVV','ZZZ',
    "/ZZZ",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','Muon_Run2022C',"/Muon_Run2022C",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','Muon_Run2022D',"/Muon_Run2022D",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2022C',"/SingleMuon_Run2022C",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  # SINGLE ELECTRON
  D('Data','EGamma_Run2022C',"/EGamma_Run2022C",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),
  D('Data','EGamma_Run2022D',"/EGamma_Run2022D",
   store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),

]
