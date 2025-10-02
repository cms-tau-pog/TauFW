from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/TauFW/nanoV10/Run2_2018/$SAMPLE"
url      = None #"root://eosuser.cern.ch/"
filelist = None #"samples/files/UL2018/$SAMPLE.txt"
samples  = [
    # DRELL-YAY
    M('DY','DYJetsToLL_M-50-madgraphMLM',
      "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    
    # TTBAR
    M('TT','TTTo2L2Nu',
      "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
    M('TT','TTToSemiLeptonic',
      "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
    M('TT','TTToHadronic',
      "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,toppt=True"),
  
    # W+JETS
    M('WJ','WJetsToLNu_HT-100To200',
      "/WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-200To400',
      "/WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-400To600',
      "/WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8',
      "/WJetsToLNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-800To1200',
      "/WJetsToLNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8',
      "/WJetsToLNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),

    M('WJetsToLNu_inclusive','WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8',
    "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
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
      "/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_tW_top_5f_NoFullyHadronicDecays',
      "/ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_t-channel_antitop_4f_InclusiveDecays',
      "/ST_t-channel_antitop_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM", 
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','ST_t-channel_top_4f_InclusiveDecays',
      "/ST_t-channel_top_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM", 
      store=storage,url=url,files=filelist,opts="useT1=True"),
  
    # DIBOSON
    M('Dibosons','WW',
      "/WW_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','WZ',
      "/WZ_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','ZZ',
      "/ZZ_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    
    # W*
    M('WMu','WToMuNu_M-200_TuneCP5_13TeV-pythia8',
      "/WToMuNu_M-200_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True"),
    M('WTau','WToTauNu_M-200_TuneCP5_13TeV-pythia8-tauola',
      "/WToTauNu_M-200_TuneCP5_13TeV-pythia8-tauola/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True",channels=['taunu']),
    
    # SINGLE MUON
    D('SingleMu_Run2018A','SingleMuon_Run2018A',"/SingleMuon/Run2018A-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('SingleMu_Run2018B','SingleMuon_Run2018B',"/SingleMuon/Run2018B-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', "munu", "wjets"]),
    D('SingleMu_Run2018C','SingleMuon_Run2018C',"/SingleMuon/Run2018C-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('SingleMu_Run2018D','SingleMuon_Run2018D',"/SingleMuon/Run2018D-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
 
  
    # MET
    D('MET_Run2018A','MET_Run2018A',"/MET/Run2018A-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),
    D('MET_Run2018B','MET_Run2018B',"/MET/Run2018B-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),
    D('MET_Run2018C','MET_Run2018C',"/MET/Run2018C-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),
    D('MET_Run2018D','MET_Run2018D',"/MET/Run2018D-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu']),

    
    # JET
    D('JetHT_Run2018A','JetHT_Run2018A',"/JetHT/Run2018A-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    D('JetHT_Run2018B','JetHT_Run2018B',"/JetHT/Run2018B-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    D('JetHT_Run2018C','JetHT_Run2018C',"/JetHT/Run2018C-UL2018_MiniAODv2_NanoAODv9-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    D('JetHT_Run2018D','JetHT_Run2018D',"/JetHT/Run2018D-UL2018_MiniAODv2_NanoAODv9-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'dijets']),
    
]
