from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None 
url      = "root://cms-xrd-global.cern.ch/" 
filelist = None 
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [
  ### SINGLE MUON DATA for Tau Trigger Studies ###

  ### MUON0 ###

  # D('Data','Muon0_Run2024A',"/Muon0/Run2024A-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  # D('Data','Muon0_Run2024B',"/Muon0/Run2024B-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024C',"/Muon0/Run2024C-2024CDEReprocessing-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024D',"/Muon0/Run2024D-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024E',"/Muon0/Run2024E-PromptReco-v1/NANOAOD","/Muon0/Run2024E-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024F',"/Muon0/Run2024F-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024G',"/Muon0/Run2024G-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024H',"/Muon0/Run2024H-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024I',"/Muon0/Run2024I-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),

  ### MUON1 ###

  # D('Data','Muon1_Run2024A',"/Muon1/Run2024A-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  # D('Data','Muon1_Run2024B',"/Muon1/Run2024B-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024C',"/Muon1/Run2024C-2024CDEReprocessing-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024D',"/Muon1/Run2024D-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024E',"/Muon1/Run2024E-PromptReco-v1/NANOAOD","/Muon1/Run2024E-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024F',"/Muon1/Run2024F-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024G',"/Muon0/Run2024G-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024H',"/Muon1/Run2024H-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024I',"/Muon1/Run2024I-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),     

]

