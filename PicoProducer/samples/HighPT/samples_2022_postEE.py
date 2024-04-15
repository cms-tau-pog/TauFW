from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE_new/$SAMPLE"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/UL2018/$SAMPLE.txt"
samples  = [
    # DRELL-YAY
    M('DY','DYto2L-4Jets_MLL-50',
      "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_1J',
      "/DYto2L-4Jets_MLL-50_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_2J',
      "/DYto2L-4Jets_MLL-50_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_3J',
      "/DYto2L-4Jets_MLL-50_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_4J',
      "/DYto2L-4Jets_MLL-50_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    
    # TTBAR
    M('TT','TTTo2L2Nu',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('TT','TTtoLNu2Q',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('TT','TTto4Q',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
  
    # W+JETS
    M('WJetsToLNu','WtoLNu-4Jets',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),   
    M('WJetsToLNu','WJetstoLNu-4Jets_1J',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),   
    M('WJetsToLNu','WJetstoLNu-4Jets_2J',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
   
    M('WJetsToLNu','WJetstoLNu-4Jets_3J',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
   
    M('WJetsToLNu','WtoLNu-4Jets_4J',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
   
    # SINGLE TOP
    M('ST','TbarWplusto2L2Nu',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TbarWplustoLNu2Q',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TWminusto2L2Nu',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TWminustoLNu2Q',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TBbarQ_t-channel',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TbarBQ_t-channel',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
  
    # DIBOSON
    M('Dibosons','WW',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','WZ',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','ZZ',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    
    # W*
    M('WMu','WtoMuNu',
      "/WtoMuNu_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True"),
    M('WTau','WtoNuTau',
      "/WtoNuTau_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True",channels=['taunu']),    


    # Zto2Nu_HT
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-100to200',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),    
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-200to400',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),    
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-400to800',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-800to1500',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    

    # WtoLNu_HT
    M('WtoLNu_HT','WtoLNu-4Jets_MLNu-0to120_HT-100to400',
      "",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WtoLNu_HT','WtoLNu-4Jets_MLNu-0to120_HT-400to800',
      "/WtoLNu-4Jets_MLNu-0to120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),

    # SINGLE MUON
    D('Muon_Run2022F','Muon_Run2022F',"/Muon/Run2022F-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('Muon_Run2022G','Muon_Run2022G',"/Muon/Run2022G-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),

    # MET
    D('JetMet_Run2022F','JetMet_Run2022F',"/JetMET/Run2022F-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu', 'dijets']),
    D('JetMet_Run2022G','JetMet_Run2022G',"/JetMET/Run2022G-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu', 'dijets']),
    
]
