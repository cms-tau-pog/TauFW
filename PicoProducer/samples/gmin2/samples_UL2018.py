from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/$DAS"
url      = "root://eosuser.cern.ch/"
filelist = "samples/files/UL2018/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  #M('DY','DYJetsToLL_M-10to50',
  #  "/DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
  #  store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYJetsToLL_M-50',
    "DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/221117_084137/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  #M('DY','DYJetsToLL_M-50_das',
  #  "/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2/NANOAODSIM"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_084158/0000",
    "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_084158/0001",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_152946/0000",
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_152946/0001",
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_152946/0002",
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_152946/0003",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToHadronic',
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_153013/0000",
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_153013/0001",
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_153013/0002",
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_153013/0003",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  
#   # W+JETS
#   M('WJ','WJetsToLNu',
#     "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('WJ','W1JetsToLNu',
#     "/W1JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     "/W1JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('WJ','W2JetsToLNu',
#     "/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     "/W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('WJ','W3JetsToLNu',
#     "/W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     "/W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('WJ','W4JetsToLNu',
#     "/W4JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   
#   # SINGLE TOP
#   M('ST','ST_tW_antitop',
#     "/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM", # BUGGY Summer19
#     "/ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('ST','ST_tW_top',
#     "/ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM", # BUGGY Summer19
#     "/ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('ST','ST_t-channel_antitop',
#     "/ST_t-channel_antitop_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM", # BUGGY Summer19
#     store=storage,url=url,files=filelist,opts="useT1=False"),
#   M('ST','ST_t-channel_top',
#     "/ST_t-channel_top_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM", # BUGGY Summer19
#     store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # DIBOSON
  M('VV','GGToWW',
    #"GGToWW_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122754/0000", # filter, 1/128
    "GGToWW_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_nofilter_januarysamples/240109_135325/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  ###M('VV','WWTo2L2Nu', # use VVTo2L2Nu instead !
  ###  "WWTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18_NanoAODv9/221117_165726/0000",
  ###  store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo2Q2L',
    "WZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/221117_170158/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo3LNu',
    "WZTo3LNu_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/221117_170327/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  ###M('VV','ZZTo2L2Nu', # use VVTo2L2Nu instead !
  ###  "ZZTo2L2Nu_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL18_NanoAODv9/221117_172331/0000",
  ###  store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2Q2L',
    "ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/221117_172209/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo4L',
    "ZZTo4L_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL18_NanoAODv9/221117_171953/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','VVTo2L2Nu',
    "VVTo2L2Nu_MLL-1toInf_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/231018_130221/0000",
    "VVTo2L2Nu_MLL-1toInf_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL18_NanoAODv9/231018_130221/0001",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SIGNAL
  M('Signal','GGToMuMu',
    #"RunIISummer20UL18_GGToMuMu/GGToMuMu/230619_092808/0000",
    #"GGToMuMu_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122720/0000", # filter, 1/128
    "GGToMuMu_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_nofilter_januarysamples/240109_135356/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('Signal','GGToEE',
    "GGToElEl_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_nofilter_januarysamples/240109_135338/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('Signal','GGToTauTau',
    #"GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_july/230724_122828/0000", # filter, 1/128
    "GGToTauTau_Ctb20_RunIISummer20UL18/RunIISummer20UL18_NanoAODv9_nofilter_januarysamples/240109_135710/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2018A',"SingleMuon/RunIISummer20UL18_NanoAODv9/221117_084105/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2018B',"SingleMuon/SingleMuon_Run2018B-RunIISummer20UL18_NanoAODv9/221118_110639/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu'],
    blacklist=[ # files with no good events in golden JSON
      "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/SingleMuon/SingleMuon_Run2018B-RunIISummer20UL18_NanoAODv9/221118_110639/0000/NanoAODv9_13.root",
      "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/SingleMuon/SingleMuon_Run2018B-RunIISummer20UL18_NanoAODv9/221118_110639/0000/NanoAODv9_25.root",
      "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/SingleMuon/SingleMuon_Run2018B-RunIISummer20UL18_NanoAODv9/221118_110639/0000/NanoAODv9_34.root",
      "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/SingleMuon/SingleMuon_Run2018B-RunIISummer20UL18_NanoAODv9/221118_110639/0000/NanoAODv9_36.root",
    ]),
  D('Data','SingleMuon_Run2018C',"SingleMuon/SingleMuon_Run2018C-RunIISummer20UL18_NanoAODv9/221118_110800/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2018D',"SingleMuon/SingleMuon_Run2018D-RunIISummer20UL18_NanoAODv9/221118_110958/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  
#   # SINGLE ELECTRON
#   D('Data','EGamma_Run2018A',"/EGamma/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
#     store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),
#   D('Data','EGamma_Run2018B',"/EGamma/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
#     store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),
#   D('Data','EGamma_Run2018C',"/EGamma/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
#     store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),
#   D('Data','EGamma_Run2018D',"/EGamma/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD",
#     store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'etau','ee']),
  
]