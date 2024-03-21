from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/irandreo/Run3_22_postEE_new/$SAMPLE"
url      = None #"root://cms-xrd-global.cern.ch/"
filelist = None #"samples/files/UL2018/$SAMPLE.txt"
samples  = [

    # SINGLE MUON
    D('Muon_Run2022F','Muon_Run2022F',"/Muon/Run2022F-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('Muon_Run2022G','Muon_Run2022G',"/Muon/Run2022G-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
  
    # MET
    D('JetMet_Run2022F','JetMet_Run2022F',"/JetMET/Run2022F-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu', 'dijets']),
    D('JetMet_Run2022G','JetMet_Run2022G',"/JetMET/Run2022G-PromptNanoAODv11_v1-v2/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'highpt', 'taunu', 'dijets']),
    
]
