from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = None #"root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = "samples/files/2024_v15/$SAMPLE.txt"
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [
  
  # DRELL-YAN 
  # M('DY','DYto2L-4Jets_MLL-50_ext1',                                                                                        
  #   "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Winter24NanoAOD-JMENano_133X_mcRun3_2024_realistic_v10_ext1-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts_dy),
  # M('DY','DYto2L-4Jets_MLL-50_ext2',                                                                                        
  #   "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Winter24NanoAOD-JMENanoV14_133X_mcRun3_2024_realistic_v10_ext2-v1/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts_dy),
  M('DY','DYto2Tau-2Jets_Bin-MLL-50',
    "/DYto2Tau-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v5/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),
  M('DY','DYto2Tau-2Jets_Bin-0J-MLL-50',
    "/DYto2Tau-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),

  M('DY','DYto2Mu-2Jets_Bin-MLL-50',
    "/DYto2Mu-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v6/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),

  M('DY','DYto2Mu-2Jets_Bin-0J-MLL-50',
    "/DYto2Mu-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),

  M('DY','DYto2E-2Jets_Bin-MLL-50',
    "/DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v4/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),

  M('DY','DYto2E-2Jets_Bin-0J-MLL-50',
    "/DYto2E-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_dy),


  # TTBAR
  M('TT','TTto2L2Nu',
    "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_tt),
  M('TT','TTtoLNu2Q',
    "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_tt),
  M('TT','TTto4Q',
    "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts_tt), 
    

  # W+JETS
  M('WJ','WtoTauNu-2Jets',
    "/WtoTauNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),
  M('WJ','WtoMuNu-2Jets',
    "/WtoMuNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3/NANOAODSIM",   
    store=storage,url=url,files=filelist,opts=opts),
  # M('WJ','WtoMuNu-2Jets_0J',
  #   "/WtoMuNu-2Jets_Bin-0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIMM",
  #   store=storage,url=url,files=filelist,opts=opts),
  M('WJ','WtoENu-2Jets',
    "/WtoENu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),


  # SINGLE TOP
  #M('ST','TBbarQ_t-channel',#temporary miss to add later
  #  "",
  #  store=storage,url=url,files=filelist,opts=opts),
  #M('ST','TbarBQ_t-channel',#temporary miss to add later
  #  "",
  #  store=storage,url=url,files=filelist,opts=opts),
#   M('ST','TWminustoLNu2Q',
#     "/TWminustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Winter24NanoAOD-JMENanoV14_133X_mcRun3_2024_realistic_v10-v2/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts=opts), 
#   M('ST','TWminusto2L2Nu',
#     "/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Winter24NanoAOD-JMENanoV14_133X_mcRun3_2024_realistic_v10-v2/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts=opts),
#   M('ST','TbarWplustoLNu2Q',
#     "/TbarWplustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Winter24NanoAOD-JMENanoV14_133X_mcRun3_2024_realistic_v10-v2/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts=opts),
#   M('ST','TbarWplusto2L2Nu',
#     "/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Winter24NanoAOD-JMENanoV14_133X_mcRun3_2024_realistic_v10-v2/NANOAODSIM",
#     store=storage,url=url,files=filelist,opts=opts),  
  
  # DIBOSON
  # M('VV','WWto2L2Nu',
  #   "/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAOD-140X_mcRun3_2024_realistic_v26-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts),
  M('VV','WWto4Q',
    "/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),
  M('VV','WWtoLNu2Q',
    "/WWtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),
  # M('VV','ZZto2L2Nu',
  #   "/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts),
  # # M('VV','ZZto2L2Q',
  # #   "/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAOD-140X_mcRun3_2024_realistic_v26-v2/NANOAODSIM",
  # #   store=storage,url=url,files=filelist,opts=opts),
  # M('VV','ZZto2Nu2Q',
  #   "/ZZto2Nu2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts),
  # M('VV','ZZto4L',
  #   "/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts),
  
  M('VV','ZZ',
    "/ZZ_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),

  # M('VV','WZto2L2Q',
  #   "/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
  #   store=storage,url=url,files=filelist,opts=opts),
  
  M('VV','WZ',
    "/WZ_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2/NANOAODSIM",
    store=storage,url=url,files=filelist,opts=opts),

  # SINGLE MUON

  D('Data','Muon0_Run2024C',"/Muon0/Run2024C-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  
  D('Data','Muon0_Run2024D',"/Muon0/Run2024D-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),

  D('Data','Muon0_Run2024E',
    "/Muon0/Run2024E-MINIv6NANOv15-v1/NANOAOD",
    # "/Muon0/Run2024E-PromptReco-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024F',"/Muon0/Run2024F-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  D('Data','Muon0_Run2024G',"/Muon0/Run2024G-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),


  D('Data','Muon0_Run2024H',"/Muon0/Run2024H-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),

  D('Data','Muon0_Run2024I',
    "/Muon0/Run2024I-MINIv6NANOv15-v1/NANOAOD",
    "/Muon0/Run2024I-MINIv6NANOv15_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),


  D('Data','Muon1_Run2024C',"/Muon1/Run2024C-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024D',"/Muon1/Run2024D-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024E',"/Muon1/Run2024E-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),
  D('Data','Muon1_Run2024F',"/Muon1/Run2024F-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),

  D('Data','Muon1_Run2024G',"/Muon1/Run2024G-MINIv6NANOv15-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),

  D('Data','Muon1_Run2024H',"/Muon1/Run2024H-MINIv6NANOv15-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),

  D('Data','Muon1_Run2024I',
    "/Muon1/Run2024I-MINIv6NANOv15-v1/NANOAOD",
    "/Muon1/Run2024I-MINIv6NANOv15_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'mutau*','mumu*','emu','mumutau','mumettau']),


  # SINGLE ELECTRON

  D('Data','EGamma0_Run2024C',"/EGamma0/Run2024C-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma0_Run2024D',"/EGamma0/Run2024D-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma0_Run2024E',"/EGamma0/Run2024E-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma0_Run2024F',"/EGamma0/Run2024F-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),
  
  D('Data','EGamma0_Run2024G',"/EGamma0/Run2024G-MINIv6NANOv15-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma0_Run2024H',"/EGamma0/Run2024H-MINIv6NANOv15-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma0_Run2024I',
    "/EGamma0/Run2024I-MINIv6NANOv15-v1/NANOAOD",
    "/EGamma0/Run2024I-MINIv6NANOv15_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma1_Run2024C',"/EGamma1/Run2024C-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma1_Run2024D',"/EGamma1/Run2024D-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma1_Run2024E',"/EGamma1/Run2024E-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),
  D('Data','EGamma1_Run2024F',"/EGamma1/Run2024F-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),
  D('Data','EGamma1_Run2024G',"/EGamma1/Run2024G-MINIv6NANOv15-v2/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma1_Run2024H',"/EGamma1/Run2024H-MINIv6NANOv15-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  D('Data','EGamma1_Run2024I',
    "/EGamma1/Run2024I-MINIv6NANOv15-v1/NANOAOD",
    "/EGamma1/Run2024I-MINIv6NANOv15_v2-v1/NANOAOD",
    store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'etau*','ee','eetau']),

  # # TAU
  # # D('Data','Tau_Run2024A',"/Tau/Run2024A-PromptReco-v1/NANOAOD",
  # #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024B',"/Tau/Run2024B-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024C',"/Tau/Run2024C-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024D',"/Tau/Run2024D-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024E',
  #   "/Tau/Run2024E-PromptReco-v1/NANOAOD",
  #   "/Tau/Run2024E-PromptReco-v2/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024F',"/Tau/Run2024F-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
  # D('Data','Tau_Run2024G',"/Tau/Run2024G-PromptReco-v1/NANOAOD",
  #   store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'tautau']),
   
]


