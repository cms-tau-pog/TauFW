from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = "/eos/cms/store/group/phys_tau/irandreo/Run3_22/$SAMPLE"
url      = None #"root://eosuser.cern.ch/"
filelist = None #"samples/files/UL2018/$SAMPLE.txt"
samples  = [
    # DRELL-YAN
    M('DY','DYto2L-4Jets_MLL-50',
      "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_1J',
      "/DYto2L-4Jets_MLL-50_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_2J',
      "/DYto2L-4Jets_MLL-50_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_3J',
      "/DYto2L-4Jets_MLL-50_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    M('DY','DYto2L-4Jets_MLL-50_4J',
      "/DYto2L-4Jets_MLL-50_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,zpt=True"),
    
    # TTBAR
    M('TT','TTTo2L2Nu',
      "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('TT','TTtoLNu2Q',
      "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('TT','TTto4Q',
      "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),  

    # W+JETS
    M('WJ','WJetsToLNu-4Jets',
      "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),   
    M('WJ','WJetsToLNu-4Jets_1J',
      "/WtoLNu-4Jets_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),   
    M('WJ','WJetsToLNu-4Jets_2J',
      "/WtoLNu-4Jets_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu-4Jets_3J',
      "/WtoLNu-4Jets_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WJ','WJetsToLNu-4Jets_4J',
      "/WtoLNu-4Jets_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
   
    # SINGLE TOP
    M('ST','TbarWplusto2L2Nu',
      "/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TbarWplustoLNu2Q',
      "/TbarWplustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TWminusto2L2Nu',
      "/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5_ext1-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TWminustoLNu2Q',
      "/TWminustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5_ext1-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TBbarQ_t-channel',
      "/TBbarQ_t-channel_4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('ST','TbarBQ_t-channel',
      "/TbarBQ_t-channel_4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
  
    # DIBOSON
    M('Dibosons','WW',
      "/WW_TuneCP5_13p6TeV_pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','WZ',
      "/WZ_TuneCP5_13p6TeV_pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Dibosons','ZZ',
      "/ZZ_TuneCP5_13p6TeV_pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    
    # W*
    M('WMu','WtoMuNu',
      "/WtoMuNu_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True"),

    M('WTau','WtoNuTau',
      "/WtoNuTau_M-200_TuneCP5_13p6TeV_pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True,dowmasswgt=True",channels=['taunu']),
        
    # Zto2Nu_HT
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-100to200',
      "/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),    
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-400to800',
      "/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('Zto2Nu_HT','Zto2Nu-4Jets_HT-800to1500',
      "/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    

    M('WtoLNu_HT','WtoLNu-4Jets_MLNu-0to120_HT-100to400',
      "/WtoLNu-4Jets_MLNu-0to120_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),
    M('WtoLNu_HT','WtoLNu-4Jets_MLNu-0to120_HT-400to800',
      "/WtoLNu-4Jets_MLNu-0to120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1/NANOAODSIM",
      store=storage,url=url,files=filelist,opts="useT1=True"),


    # SINGLE MUON
    D('SingleMuon_Run2022C','SingleMuon_Run2022C',
      "/SingleMuon_Run2022C/Run2022C-ReRecoNanoAODv11-v1/NANOAO",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('Muon_Run2022C','Muon_Run2022C',
      "/Muon/Run2022C-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('Muon_Run2022D','Muon_Run2022D',
      "/Muon/Run2022D-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
    D('Muon_Run2022E','Muon_Run2022E',
      "/Muon/Run2022E-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'mutau','mumu','emu','highpt', 'munu', 'wjets']),
 
  
    # MET
    D('JetMet_Run2022C','JetMet_Run2022C',"/JetMET/Run2022C-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'munu', 'taunu', 'dijets']),
    D('JetMet_Run2022D','JetMet_Run2022D',"/JetMET/Run2022D-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'munu', 'taunu', 'dijets']),
    D('JetMet_Run2022E','JetMet_Run2022E',"/JetMET/Run2022E-ReRecoNanoAODv11-v1/NANOAOD",
      store=storage,url=url,files=filelist,opts="useT1=False",channels=["skim*",'munu', 'taunu', 'dijets']),
    
]
