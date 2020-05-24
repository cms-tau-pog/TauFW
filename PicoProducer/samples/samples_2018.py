from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
samples = [
  
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext1-v1/NANOAODSIM",
    "/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16NanoAODv6-PUMoriond17_Nano25Oct2019_102X_mcRun2_asymptotic_v7_ext2-v1/NANOAODSIM",
  ),
  
  D('SingleMuon','SingleMuon_Run2016C',
    "/SingleMuon/Run2016C-Nano25Oct2019-v1/NANOAOD",
  ),
  
]
