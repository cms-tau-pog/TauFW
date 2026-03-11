from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/2023D/$SAMPLE.txt"
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [

  ### SINGLE MUON DATA for Tau Trigger Studies ###

  ### MUON0 ###

  # D('Data','Muon0_Run2025B',"/Muon0/Run2025B-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),  
  D('Data','Muon0_Run2025C',"/Muon0/Run2025C-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2025D',"/Muon0/Run2025D-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2025E',"/Muon0/Run2025E-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2025F',"/Muon0/Run2025F-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2025G',"/Muon0/Run2025G-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),

  ### MUON1 ###

  # D('Data','Muon1_Run2025B',"/Muon1/Run2025B-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']), 
  D('Data','Muon1_Run2025C',"/Muon1/Run2025C-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   
  D('Data','Muon1_Run2025D',"/Muon1/Run2025D-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2025E',"/Muon1/Run2025E-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   
  D('Data','Muon1_Run2025F',"/Muon1/Run2025F-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   
  D('Data','Muon1_Run2025G',"/Muon1/Run2025G-PromptReco-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau','mumu','emu','mumutau','mumettau']),   

]

