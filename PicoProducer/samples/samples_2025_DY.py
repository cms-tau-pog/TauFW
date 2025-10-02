from TauFW.PicoProducer.storage.Sample import MC as M
from TauFW.PicoProducer.storage.Sample import Data as D
storage  = None #"/eos/cms/store/group/phys_tau/irandreo/Run3_23D/$DAS"
url      = "root://cms-xrd-global.cern.ch/" #"root://eosuser.cern.ch/"
filelist = None #"samples/files/2023D/$SAMPLE.txt"
opts     = "useT1=False,dojec=False"
opts_dy  = opts+",zpt=True"
opts_tt  = opts+",toppt=True"
samples  = [

  # DRELL-YAN 
  M('DY','DYto2Tau-4Jets_Bin-MLL-50_Fil-MuTauh',
  "/DYto2Tau-4Jets_Bin-MLL-50_Fil-MuTauh_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Winter25NanoAOD-142X_mcRun3_2025_realistic_v7-v2/NANOAODSIM",
  store=storage,url=url,files=filelist,opts=opts_dy)
]