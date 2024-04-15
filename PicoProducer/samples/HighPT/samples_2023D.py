from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/2023D/$SAMPLE.txt"
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
opts_wstar = opts+",dowmasswgt=True"
samples  = [
  
    # DRELL-YAN 
    M('DY','DYto2L-4Jets_MLL-50',
      "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_dy),
    M('DY','DYto2L-4Jets_MLL-50_1J',
      "/DYto2L-4Jets_MLL-50_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_dy),
    M('DY','DYto2L-4Jets_MLL-50_2J',
      "/DYto2L-4Jets_MLL-50_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_dy),
    M('DY','DYto2L-4Jets_MLL-50_3J',
      "/DYto2L-4Jets_MLL-50_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_dy),
    M('DY','DYto2L-4Jets_MLL-50_4J',
      "/DYto2L-4Jets_MLL-50_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_dy), 
  
    # TTBAR
    M('TT','TTto2L2Nu',
      "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_tt),
    M('TT','TTtoLNu2Q',
      "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_tt),
    M('TT','TTto4Q',
      "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_tt),
  
    # W+JETS
    M('WJ','WtoLNu-4Jets',
      "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('WJ','WtoLNu-4Jets_1J',
      "/WtoLNu-4Jets_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('WJ','WtoLNu-4Jets_2J',
      "/WtoLNu-4Jets_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('WJ','WtoLNu-4Jets_3J',
      "/WtoLNu-4Jets_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('WJ','WtoLNu-4Jets_4J',
      "/WtoLNu-4Jets_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    
    # SINGLE TOP
    #M('ST','TBbarQ_t-channel',#temporary miss to add later
    #  "",
    #  store=storage,url=url,files=filelist,opts=opts),
    #M('ST','TbarBQ_t-channel',#temporary miss to add later
    #  "",
    #  store=storage,url=url,files=filelist,opts=opts),
    M('ST','TWminustoLNu2Q',
      "/TWminustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('ST','TWminusto2L2Nu',
      "/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('ST','TbarWplustoLNu2Q',
      "/TbarWplustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('ST','TbarWplusto2L2Nu',
      "/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts), 
    
    # DIBOSON
    M('VV','WW',
      "/WW_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('VV','WZ',
      "/WZ_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('VV','ZZ',
      "/ZZ_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),

    # Z->vv
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-100to200',
      "/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-200to400',
      "/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-400to800',
      "/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-800to1500',
      "/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),

    # W->lnu HT binned
    M('WtoLNu_HT100to400','WtoLNu_HT100to400',
      "/WtoLNu-4Jets_MLNu-0to120_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),
    M('WtoLNu_HT400to800','WtoLNu_HT400to800',
      "/WtoLNu-4Jets_MLNu-0to120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts),

    # W->taunu
    M('WtoNuTau','WtoNuTau',
      "/WtoNuTau_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_wstar),
    # W->munu
    M('WtoMuNu','WtoMuNu',
      "/WtoMuNu_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts=opts_wstar),

    # JetMET
    D('JetMET','JetMET0_v1',"/JetMET0/Run2023D-22Sep2023_v1-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'taunu','dijets']),
    D('JetMET','JetMET0_v2',"/JetMET0/Run2023D-22Sep2023_v2-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'taunu','dijets']),
    D('JetMET','JetMET1_v1',"/JetMET1/Run2023D-22Sep2023_v1-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'taunu','dijets']),
    D('JetMET','JetMET1_v2',"/JetMET1/Run2023D-22Sep2023_v2-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'taunu','dijets']),
        
    # SINGLE MUON
    D('Muon','Muon0_v1',"/Muon0/Run2023D-22Sep2023_v1-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'munu','wjets']),
    D('Muon','Muon0_v2',"/Muon0/Run2023D-22Sep2023_v2-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'munu','wjets']),
    D('Muon','Muon1_v1',"/Muon1/Run2023D-22Sep2023_v1-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'munu','wjets']),
    D('Muon','Muon1_v2',"/Muon1/Run2023D-22Sep2023_v2-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts=opts,channels=["skim*",'munu','wjets']),
   
]
