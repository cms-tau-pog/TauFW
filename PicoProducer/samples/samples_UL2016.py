from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/user/${USER::1}/$USER/samples/nano/$ERA/$DAS"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/UL2016/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  #M('DY','DYJetsToLL_M-10to50',
  #  "/DYJetsToLL_M-10to50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7-v1/NANOAODSIM",
  #  store=storage,url=url,files=filelist,opts='zpt=True',),
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  M('DY','DY1JetsToLL_M-50',
    "/DY1JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  M('DY','DY2JetsToLL_M-50',
    "/DY2JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  M('DY','DY3JetsToLL_M-50',
    "/DY3JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  M('DY','DY4JetsToLL_M-50',
    "/DY4JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  M('DY','DYJetsToMuTauh_M-50',
    "/DYJetsToTauTauToMuTauh_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts='zpt=True'),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist,opts='toppt=True'),
  M('TT','TTToSemiLeptonic',
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist,opts='toppt=True'),
  M('TT','TTToHadronic',
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist,opts='toppt=True'),
  
  # W+JETS
  M('WJ','WJetsToLNu',
    "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist),
  M('WJ','W1JetsToLNu',
    "/W1JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  M('WJ','W2JetsToLNu',
    "/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  M('WJ','W3JetsToLNu',
    "/W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  M('WJ','W4JetsToLNu',
    "/W4JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  
  # SINGLE TOP
  M('ST','ST_tW_antitop',
    "/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,blacklist=[
      "/store/mc/RunIISummer19UL16NanoAODv2/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/NANOAODSIM/106X_mcRun2_asymptotic_v15-v1/280000/213C8681-C6B9-A746-BFE4-1AA26E94E5C0.root",
    ]),
  M('ST','ST_tW_top',
    "/ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  M('ST','ST_t-channel_antitop',
    "/ST_t-channel_antitop_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  M('ST','ST_t-channel_top',
    "/ST_t-channel_top_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  
  # DIBOSON
  M('VV','WW',
    "/WW_TuneCP5_13TeV-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/WW_TuneCP5_13TeV-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist),
  M('VV','WZ',
    "/WZ_TuneCP5_13TeV-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer19
    "/WZ_TuneCP5_13TeV-pythia8/RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM", # Summer20
    store=storage,url=url,files=filelist),
  M('VV','ZZ',
    "/ZZ_TuneCP5_13TeV-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM",
    store=storage,url=url,files=filelist),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2016F',"/SingleMuon/Run2016F-UL2016_MiniAODv1_NanoAODv2-v4/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016G',"/SingleMuon/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016H',"/SingleMuon/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'mutau','mumu','emu']),
  
  # SINGLE ELECTRON
  D('Data','SingleElectron_Run2016F',"/SingleElectron/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'etau','ee']),
  D('Data','SingleElectron_Run2016G',"/SingleElectron/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'etau','ee']),
  D('Data','SingleElectron_Run2016H',"/SingleElectron/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'etau','ee']),
  
  # TAU
  D('Data','Tau_Run2016F',"/Tau/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'tautau']),
  D('Data','Tau_Run2016G',"/Tau/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'tautau']),
  D('Data','Tau_Run2016H',"/Tau/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD",
    store=storage,url=url,files=filelist,channels=["skim*",'tautau']),
  
]