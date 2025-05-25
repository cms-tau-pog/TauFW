from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None 
url      = "root://cms-xrd-global.cern.ch/" 
filelist = None 
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [
    
  # SINGLE MUON
  D('Data','Muon0_v2',"/Muon0/Run2024I-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  # D('Data','Muon0_v1',"/Muon0/Run2024I-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  # D('Data','Muon1_v1',"/Muon1/Run2024I-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_v2',"/Muon1/Run2024I-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
     
]
