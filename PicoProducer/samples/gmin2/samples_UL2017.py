from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/$DAS"
url      = "root://eosuser.cern.ch/"
filelist = "samples/files/UL2017/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  #M('DY','DYJetsToLL_M-10to50',
  #  "/DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM",
  #  store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  M('DY','DYJetsToLL_M-50',
    "DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17_NanoAODv9/230413_082310/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  #M('DY','DYJetsToLL_M-50_das',
  #  "/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17NanoAODv9-106X_mc2017_realistic_v9-v2/NANOAODSIM"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17_NanoAODv9/230413_082708/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17_NanoAODv9/230413_082733/0000",
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17_NanoAODv9/230413_082733/0001",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToHadronic',
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17_NanoAODv9/230413_082721/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  
  # DIBOSON
  M('VV','GGToWW',
    #"GGToWW_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_july/230724_122937/0000", # filter, 1/128
    "GGToWW_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_nofilter_januarysamples/240109_135306/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  ###M('VV','WWTo2L2Nu', # use VVTo2L2Nu instead !
  ###  "WWTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL17_NanoAODv9/230413_082948/0000",
  ###  store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo2Q2L',
    "WZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17_NanoAODv9/230413_082959/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo3LNu',
    "WZTo3LNu_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17_NanoAODv9/230413_083010/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  ###M('VV','ZZTo2L2Nu', # use VVTo2L2Nu instead !
  ###  "ZZTo2L2Nu_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL17_NanoAODv9/230413_083022/0000",
  ###  store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2Q2L',
    "ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17_NanoAODv9/230413_083036/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo4L',
    "ZZTo4L_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL17_NanoAODv9/230413_083049/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','VVTo2L2Nu',
    "VVTo2L2Nu_MLL-1toInf_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL17_NanoAODv9/231018_130301/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SIGNAL
  M('Signal','GGToMuMu',
    #"RunIISummer20UL17_GGToMuMu/RunIISummer20UL17_NanoAODv9/230619_120555/0000",
    #"GGToMuMu_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_july/230724_122907/0000", # filter, 1/128
    "GGToMuMu_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_nofilter_januarysamples/240109_135255/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('Signal','GGToEE',
    "GGToElEl_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_nofilter_januarysamples/240109_135239/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('Signal','GGToTauTau',
    "GGToTauTau_Ctb20_RunIISummer20UL17/RunIISummer20UL17_NanoAODv9_nofilter_januarysamples/240109_135217/0000", # 1/137, no filter
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2017C',"SingleMuon/SingleMuon_Run2017C-RunIISummer20UL17_NanoAODv9/230413_082620/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2017D',"SingleMuon/SingleMuon_Run2017D-RunIISummer20UL17_NanoAODv9/230413_082632/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2017E',"SingleMuon/SingleMuon_Run2017E-RunIISummer20UL17_NanoAODv9/230413_082644/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2017F',"SingleMuon/SingleMuon_Run2017F-RunIISummer20UL17_NanoAODv9/230413_082655/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  
]