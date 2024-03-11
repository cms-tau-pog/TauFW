from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = None #"root://eosuser.cern.ch/"
filelist = "samples/files/2023D/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN ##binned ones requested but still pending 
  M('DY','DYto2L-4Jets_MLL-50',                                                                                                         
    "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_1J',
    "/DYto2L-4Jets_MLL-50_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_2J',
    "/DYto2L-4Jets_MLL-50_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_3J',
    "/DYto2L-4Jets_MLL-50_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
  M('DY','DYto2L-4Jets_MLL-50_4J',
    "/DYto2L-4Jets_MLL-50_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"), 
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  M('TT','TTToHadronic',
    "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  
  # W+JETS requested, still not completed
  M('WJ','WtoLNu-4Jets',
    "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('WJ','WtoLNu-4Jets_1J',
    "/WtoLNu-4Jets_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('WJ','WtoLNu-4Jets_2J',
    "/WtoLNu-4Jets_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('WJ','WtoLNu-4Jets_3J',
    "/WtoLNu-4Jets_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('WJ','WtoLNu-4Jets_4J',
    "/WtoLNu-4Jets_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  
  # SINGLE TOP
  #M('ST','TBbarQ_t-channel',#temporary miss to add later
  #  "",
  #  store=storage,url=url,files=filelist,opts="useT1=False"),
  #M('ST','TbarBQ_t-channel',#temporary miss to add later
  #  "",
  #  store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TWminustoLNu2Q',
    "/TWminustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TWminusto2L2Nu',
    "/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TbarWplustoLNu2Q',
    "/TbarWplustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v5-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('ST','TbarWplusto2L2Nu',
    "/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v5-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"), 
  
  # DIBOSON
  M('VV','WW',
    "/WW_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VV','WZ',
    "/WZ_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  M('VV','ZZ',
    "/ZZ_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=True"),
  
  # SINGLE MUON
  D('Data','Muon0_v1',"/Muon0/Run2023D-22Sep2023_v1-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_v2',"/Muon0/Run2023D-22Sep2023_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_v1',"/Muon1/Run2023D-22Sep2023_v1-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_v2',"/Muon1/Run2023D-22Sep2023_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
   
  
  # SINGLE ELECTRON
  D('Data','EGamma0_v1',"/EGamma0/Run2023D-22Sep2023_v1-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee','eetau']),
  D('Data','EGamma0_v2',"/EGamma0/Run2023D-22Sep2023_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee','eetau']),
  D('Data','EGamma1_v1',"/EGamma1/Run2023D-22Sep2023_v1-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee','eetau']),
  D('Data','EGamma1_v2',"/EGamma1/Run2023D-22Sep2023_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee','eetau']),
  
  # TAU
  D('Data','Tau_v1',"/Tau/Run2023D-22Sep2023_v1-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'tautau']),
  D('Data','Tau_v2',"/Tau/Run2023D-22Sep2023_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'tautau']),
   
]
