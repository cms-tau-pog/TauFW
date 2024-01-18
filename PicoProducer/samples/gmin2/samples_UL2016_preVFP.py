from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/cmst3/group/taug2/reNanoAOD/$DAS"
url      = "root://eosuser.cern.ch/"
filelist = "samples/files/UL2016_preVFP/$SAMPLE.txt"
samples  = [
  
  # DRELL-YAN
  M('DY','DYJetsToLL_M-50',
    "DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_082615/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,zpt=True"),
  
  # TTBAR
  M('TT','TTTo2L2Nu',
    "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083329/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToSemiLeptonic',
    "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083356/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  M('TT','TTToHadronic',
    "TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083342/0000",
    store=storage,url=url,files=filelist,opts="useT1=False,toppt=True"),
  
  # DIBOSON
  M('VV','WWTo2L2Nu',
    "WWTo2L2Nu_TuneCP5_13TeV-powheg-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083619/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo2Q2L',
    "WZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083632/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','WZTo3LNu',
    "WZTo3LNu_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083645/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2L2Nu',
    "ZZTo2L2Nu_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083658/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo2Q2L',
    "ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083712/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','ZZTo4L',
    "ZZTo4L_TuneCP5_13TeV_powheg_pythia8/RunIISummer20UL16APV_NanoAODv9/230420_083725/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','GGToWW',
    "GGToWW_RunIISummer20UL16APV/RunIISummer20UL16APV_NanoAODv9_july/230803_074038/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  M('VV','VVTo2L2Nu',
    "VVTo2L2Nu_MLL-1toInf_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIISummer20UL16APV_NanoAODv9/231018_130414/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SIGNAL
  M('Signal','GGToMuMu',
    "GGToMuMu_RunIISummer20UL16APV/RunIISummer20UL16APV_NanoAODv9_july/230803_074000/0000",
    store=storage,url=url,files=filelist,opts="useT1=False"),
  
  # SINGLE MUON
  D('Data','SingleMuon_Run2016B',"SingleMuon/SingleMuon_Run2016preB-RunIISummer20UL16APV_NanoAODv9/230420_083226/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016C',"SingleMuon/SingleMuon_Run2016preC-RunIISummer20UL16APV_NanoAODv9/230420_083239/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016D',"SingleMuon/SingleMuon_Run2016preD-RunIISummer20UL16APV_NanoAODv9/230420_083252/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016E',"SingleMuon/SingleMuon_Run2016preE-RunIISummer20UL16APV_NanoAODv9/230420_083304/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  D('Data','SingleMuon_Run2016F',"SingleMuon/SingleMuon_Run2016preF-RunIISummer20UL16APV_NanoAODv9/230420_083317/0000",
    store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu']),
  
]