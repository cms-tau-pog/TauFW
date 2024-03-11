from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/TauFW/nano/UL2018/$DAS"
url      = None #"root://eosuser.cern.ch/"
filelist = "samples/files/2018UL/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1_ext1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToHadronic',
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  
  # W+JETS
  M('WJ','WJetsToLNu',
    "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
    
  # DIBOSON
  M('VV','WW',
    "/WW_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZ',
    "/WZ_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZ',
    "/ZZ_TuneCP5_13TeV-pythia8/RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1/NANOAODSIM",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2018A',"/SingleMuon/Run2018A-UL2018_MiniAODv1_NanoAODv2-v3/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','SingleMuon_Run2018B',"/SingleMuon/Run2018B-UL2018_MiniAODv1_NanoAODv2-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','SingleMuon_Run2018C',"/SingleMuon/Run2018C-UL2018_MiniAODv1_NanoAODv2-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','SingleMuon_Run2018D',"/SingleMuon/Run2018D-UL2018_MiniAODv1_NanoAODv2-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
    
]
