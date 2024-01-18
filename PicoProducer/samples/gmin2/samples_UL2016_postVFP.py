from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/$DAS"
url      = "root://eosuser.cern.ch/"
filelist = "samples/files/UL2016_postVFP/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16_NanoAODv9/230421_133726/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  #M('DY','DYJetsToLL_M-50_das',
  #  "/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16NanoAODv9-106X_mcRun2_asymptotic_v17-v1/NANOAODSIM"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16_NanoAODv9/230421_134350/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16_NanoAODv9/230421_134431/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToHadronic',
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16_NanoAODv9/230421_134409/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  
  # DIBOSON
  M('VV','WWTo2L2Nu',
    "WWTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16_NanoAODv9/230421_134735/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo2Q2L',
    "WZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16_NanoAODv9/230421_134805/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo3LNu',
    "WZTo3LNu_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16_NanoAODv9/230421_134827/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2L2Nu',
    "ZZTo2L2Nu_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL16_NanoAODv9/230421_134848/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2Q2L',
    "ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16_NanoAODv9/230421_134909/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo4L',
    "ZZTo4L_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL16_NanoAODv9/230421_134935/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','GGToWW',
    "GGToWW_RunIISummer20UL16/RunIISummer20UL16_NanoAODv9_july/230803_074118/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','VVTo2L2Nu',
    "VVTo2L2Nu_MLL-1toInf_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16_NanoAODv9/231018_130335/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SIGNAL
  M('Signal','GGToMuMu',
    "GGToMuMu_RunIISummer20UL16/RunIISummer20UL16_NanoAODv9_july/230803_074103/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2016F',"SingleMuon/SingleMuon_Run2016postF-RunIISummer20UL16_NanoAODv9/230421_134259/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016G',"SingleMuon/SingleMuon_Run2016postG-RunIISummer20UL16_NanoAODv9/230421_134317/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016H',"SingleMuon/SingleMuon_Run2016postH-RunIISummer20UL16_NanoAODv9/230421_134331/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  
]