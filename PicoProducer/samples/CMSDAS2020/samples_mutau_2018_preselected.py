from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = '/eos/cms/store/group/phys_tau/CMSDAS2020/nano/2018/$DAS'
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/2016/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='zpt=True',
  ),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "/TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToSemiLeptonic',
    "/TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext3-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  M('TT','TTToHadronic',
    "/TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext2-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,opts='toppt=True',
  ),
  
  # W+JETS
  M('WJ','WJetsToLNu',
    "/WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  
  # SINGLE TOP
  M('ST','ST_tW_antitop',
    "/ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  M('ST','ST_tW_top',
    "/ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20_ext1-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  M('ST','ST_t-channel_antitop',
    "/ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  M('ST','ST_t-channel_top',
    "/ST_t-channel_top_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  
  # DIBOSON
  M('VV','WW',
    "/WW_TuneCP5_13TeV-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  M('VV','WZ',
    "/WZ_TuneCP5_13TeV-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  M('VV','ZZ',
    "/ZZ_TuneCP5_13TeV-pythia8/RunIIAutumn18NanoAODv6-Nano25Oct2019_102X_upgrade2018_realistic_v20-v1/NANOAODSIM",
    store=storage,url=url,file=filelist,
  ),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2018A',"/SingleMuon/Run2018A-Nano25Oct2019-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=["skim*",'mutau','mumu','emu'],
  ),
  D('Data','SingleMuon_Run2018B',"/SingleMuon/Run2018B-Nano25Oct2019-v1/NANOAOD",
    store=storage,url=url,file=filelist,channels=["skim*",'mutau','mumu','emu'],
  ),
  D('Data','SingleMuon_Run2018C',"/SingleMuon/Run2018C-Nano25Oct2019-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=["skim*",'mutau','mumu','emu'],
  ),
  D('Data','SingleMuon_Run2018D',"/SingleMuon/Run2018D-Nano25Oct2019-v1/NANOAOD",
   store=storage,url=url,file=filelist,channels=["skim*",'mutau','mumu','emu'],
  ),
]
