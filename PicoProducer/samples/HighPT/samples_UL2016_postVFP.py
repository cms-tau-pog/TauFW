from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/TauFW/nanoV10/Run2_2016/$SAMPLE"
url      = None #"root://eosuser.cern.ch/"
filelist = None #"samples/files/UL2016/$SAMPLE.txt"
samples  = [
    # DRELL-YAN
    M('DY','DYJetsToLL_M-50-madgraphMLM',
      "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9_ext1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    
    # TTBAR
    M('TT','TTTo2L2Nu',
      "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
    M('TT','TTToSemiLeptonic',
      "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
    M('TT','TTToHadronic',
      "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  
    # W+JETS
    M('WJ','WJetsToLNu_HT-100To200',
      "/WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-200To400',
      "/WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-400To600',
      "/WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-600To800',
      "/WJetsToLNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-800To1200',
      "/WJetsToLNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-1200To2500',
      "/WJetsToLNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),

    M('WJetsToLNu_inclusive','WJetsToLNu',
      "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
   
    # Z+JETSToNuNu
    M('ZJ','ZJetsToNuNu_HT-100To200',
      "/ZJetsToNuNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ZJ','ZJetsToNuNu_HT-200To400',
      "/ZJetsToNuNu_HT-200To600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ZJ','ZJetsToNuNu_HT-400To600',
      "/ZJetsToNuNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ZJ','ZJetsToNuNu_HT-600To800',
      "/ZJetsToNuNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ZJ','ZJetsToNuNu_HT-800To1200',
      "/ZJetsToNuNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ZJ','ZJetsToNuNu_HT-1200To2500',
      "/ZJetsToNuNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    
    # SINGLE TOP
    M('ST','ST_tW_antitop_5f_NoFullyHadronicDecays',
      "/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_tW_top_5f_NoFullyHadronicDecays',
      "/ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_t-channel_antitop_4f_InclusiveDecays',
      "/ST_t-channel_antitop_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_t-channel_top_4f_InclusiveDecays',
      "/ST_t-channel_top_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
  
    # DIBOSON
    M('Dibosons','WW',
      "/WW_TuneCP5_13TeV-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','WZ',
      "/WZ_TuneCP5_13TeV-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','ZZ',
      "/ZZ_TuneCP5_13TeV-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    
    # W*
    M('WMu','WToMuNu_M-200',
      "/WToMuNu_M-200_TuneCP5_13TeV-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True"),
    M('WTau','WToTauNu_M-200',
      "/WToTauNu_M-200_TuneCP5_13TeV-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True",channels=['taunu']),
    
    # SINGLE MUON
    D('SingleMu_Run2016F','SingleMuon_Run2016F',"/SingleMuon/Run2017F-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('SingleMu_Run2016G','SingleMuon_Run2016G',"/SingleMuon/Run2017G-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('SingleMu_Run2016H','SingleMuon_Run2016H',"/SingleMuon/Run2017H-UL2017_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
 
  
    # MET
    D('MET_Run2016F','MET_Run2016F',"/MET/Run2016F-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),
    D('MET_Run2016G','MET_Run2016G',"/MET/Run2016G-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),
    D('MET_Run2016H','MET_Run2016H',"/MET/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),

    
    # JET
    D('JetHT_Run2016F','JetHT_Run2016F',"/JetHT/Run2016F-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    D('JetHT_Run2016G','JetHT_Run2016G',"/JetHT/Run2016G-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    D('JetHT_Run2016H','JetHT_Run2016H',"/JetHT/Run2016H-UL2016_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets'])
    
]
