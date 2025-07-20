from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/2023D/$SAMPLE.txt"
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [
  

  # SINGLE MUON
  D('Data','Muon0_Run2025C',"/Muon0/Run2025C-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2025C',"/Muon1/Run2025C-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   
  D('Data','Muon0_Run2025B',"/Muon0/Run2025B-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2025B',"/Muon1/Run2025B-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   
]

