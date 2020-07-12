from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/user/i/ineuteli/samples/nano/$ERA/$PATH"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/2016/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_v1-DeepTauv2p1_TauPOG-v1/USER",
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv5_PU2017RECOSIMstep_12Apr2018_ext1_v1-DeepTauv2p1_TauPOG-v1/USER",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY1JetsToLL_M-50',
    "/DY1JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_new_pmx_102X_mc2017_realistic_v7-v1/NANOAODSIM",
    "/DY1JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_v3_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY2JetsToLL_M-50',
    "/DY2JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7-v1/NANOAODSIM",
    "/DY2JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_new_pmx_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY3JetsToLL_M-50',
    "/DY3JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7-v1/NANOAODSIM",
    "/DY3JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_new_pmx_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DY4JetsToLL_M-50',
    "/DY4JetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_v2_102X_mc2017_realistic_v7-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  M('DY','DYJetsToLL_M-10to50',
    "/DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7-v2/NANOAODSIM",
    "/DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_new_pmx_102X_mc2017_realistic_v7-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToSemiLeptonic',
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_102X_mc2017_realistic_v7_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToHadronic',
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIIFall17NanoAODv6-PU2017_12Apr2018_Nano25Oct2019_new_pmx_102X_mc2017_realistic_v7-v2/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2017B', "/SingleMuon/Run2017B-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2017C', "/SingleMuon/Run2017C-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2017D', "/SingleMuon/Run2017D-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2017E', "/SingleMuon/Run2017E-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  D('Data','SingleMuon_Run2017F', "/SingleMuon/Run2017F-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=['mutau','mumu'],
  ),
  
]