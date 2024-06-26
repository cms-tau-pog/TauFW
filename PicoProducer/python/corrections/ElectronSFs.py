# Author: Paola Mastrapasqua (June 2024)
# HTT: https://github.com/CMS-HTT/LeptonEfficiencies
# MuonPOG: https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master/Run2
# https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIRecommendations
# https://twiki.cern.ch/twiki/bin/view/CMS/EgammaRunIIIRecommendations
# correctionlib:
#   https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration     # central XPOG repo
#   https://gitlab.cern.ch/cms-egamma/auto-correctionlib-json  # early EGammaPOG releases
#   https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/ # JSON contents
#   correction summary data/jsonpog/POG/EGM/*/electron.json.gz # JSON contents (ID SFs)
#   correction summary data/jsonpog/POG/EGM/*/electronHlt.json.gz # JSON contents (Trig SFs) 
#   Example: https://github.com/cms-cat/nanoAOD-tools-modules/blob/master/python/modules/electronSF.py

import os, re
from TauFW.common.tools.log import Logger
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.corrections.ScaleFactorTool import ScaleFactorHTT
from correctionlib import CorrectionSet

pathHTT = os.path.join(datadir,"lepton/HTT/Electron/")
pathPOG = os.path.join(datadir,"jsonpog/POG/EGM/") # JSON files from central XPOG

LOG = Logger('ElectronSF')


def getcorr(corrset,sfname,abseta=False,verb=0):
  """Help function to extract Correction object and
  check if Correction inputs are what we expect them to be."""
  keys = list(corrset.keys())
  LOG.insist(sfname in keys, "Did not find key %r in correctionset! Available keys: %r"%(sfname,keys))
  corr   = corrset[sfname]
  inputs = [i.name for i in corr._base.inputs]
  eta    = 'eta' #'abseta' if abseta else 'eta' 
  #LOG.insist(len(inputs)==3,    "Expected len(inputs)==3, but got %s... Inputs: %s"%(len(inputs),inputs))
  #LOG.insist(eta in inputs[0],  "Expected %s as first input, but got %s! All inputs for %s: %s"%(eta,inputs[0],sfname,inputs))
  #LOG.insist('pt' in inputs[1], "Expected pt as second input, but got %s! All inputs for %s: %s"%(inputs[1],sfname,inputs))
  return corr
  

class ElectronSFs:
  
  def __init__(self, era, sf_id=None, sf_trig=None, flags=[ ], verb=0):
    """Prepare electron SFs from JSON files."""
    
    # SETTINGS
    fname_id = None
    fname_trig = None
    #abseta      = True 
    sf_id_   = "Electron-ID-SF" # default in Run 3
    sf_trig_ = "Electron-HLT-SF" # default in Run 3
    self.wp_trig = "HLT_SF_Ele30_MVAiso90ID" # default in Run 3
    self.wp_id   = "wp90iso" # default in Run 3
    
    if 'UL' in era:
      sf_id_       = "UL-Electron-ID-SF" # default in Run 2
      self.wp_id   = "wp90noiso" # default in Run 2
      sf_trig_     = "ele_trig"  # default in Run 2
      if '2016' in era and 'preVFP' in era:
         fname_id = pathPOG+"2016preVFP_UL/electron.json.gz"
         self.year_SF = "2016preVFP"
         fname_trig = pathHTT+"Run2016_legacy/Electron_Run2016_legacy_Ele25.root"
      elif '2016' in era:
         fname_id = pathPOG+"2016postVFP_UL/electron.json.gz"
         self.year_SF = "2016postVFP" 
         fname_trig = pathHTT+"Run2016_legacy/Electron_Run2016_legacy_Ele25.root"
      elif '2017' in era:
         fname_id = pathPOG+"2017_UL/electron.json.gz"
         self.year_SF = "2017" 
         fname_trig = pathHTT+"Run2017/Electron_Ele35.root"
      elif '2018' in era:
         fname_id = pathPOG+"2018_UL/electron.json.gz"
         self.year_SF = "2018"
         fname_trig = pathHTT+"Run2018/Electron_Run2018_Ele32orEle35.root"
    else: # Run-3
      if re.search(r"2022([C-D]|.*pre)",era): # 2022CD (preEE)
        fname_id = pathPOG+"2022_Summer22/electron.json.gz"
        fname_trig = pathPOG+"2022_Summer22/electronHlt.json.gz"
        self.year_SF    = "2022Re-recoBCD"
      elif re.search(r"2022([E-G]|.*post)",era): # 2022EFG (postEE)
        fname_id = pathPOG+"2022_Summer22EE/electron.json.gz"
        fname_trig = pathPOG+"2022_Summer22EE/electronHlt.json.gz"
        self.year_SF    = "2022Re-recoE+PromptFG"
      elif re.search(r"2023(C|.*pre)",era): # 2024C (preBPIX)
        fname_id = pathPOG+"2023_Summer23/electron.json.gz"
        fname_trig = pathPOG+"2023_Summer23/electronHlt.json.gz"
        self.year_SF    = "2023PromptC" 
      elif re.search(r"2023(D|.*post)",era): # 2024D (postBPIX)
        fname_id = pathPOG+"2023_Summer23BPix/electron.json.gz"
        fname_trig = pathPOG+"2023_Summer23BPix/electronHlt.json.gz"
        self.year_SF    ="2023PromptD"
    # DEFAULTS
    if sf_id==None:
      sf_id = sf_id_
    if sf_trig==None: 
      sf_trig = sf_trig_
    
    # CHECKS
    if verb>=0:
      print("Loading Trigger ElectronSF for era=%r, trig=%r, from %s..."%(era,sf_trig,fname_trig))
      print("Loading Id+Reco ElectronSF for era=%r, id=%r,   from %s..."%(era,sf_id,fname_id))
    if not os.path.exists(fname_id):
      LOG.throw(OSError,"ElectronSFs: fname_id=%s does not exist! Please make sure you have installed the correctionlib JSON data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"%(fname_id,datadir))
    if not os.path.exists(fname_trig):
      LOG.throw(OSError,"ElectronSFs: fname_trig=%s does not exist! "
                         "If you running with Run2 data --> Please make sure you have installed the HTT lepton ROOT data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"
                        "If you running with Run3 data --> lease make sure you have installed the correctionlib JSON data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"%(fname_trig,datadir,fname_id,datadir ))
    
    # LOAD CORRECTIONS
    corrset_id = CorrectionSet.from_file(fname_id) # load JSON
    self.sftool_id  = getcorr(corrset_id,sf_id,verb=verb) 
    if 'UL' in era:
       self.sftool_trig = ScaleFactorHTT(fname_trig,'ZMass',sf_trig,verb=verb)
    else:
       corrset_trig = CorrectionSet.from_file(fname_trig) 
       self.sftool_trig = getcorr(corrset_trig,sf_trig,verb=verb) 
    
  
  def getTriggerSF(self, pt, eta, syst='sf'):
    """Get SF for single electron trigger.
    Use syst='sfup', 'sfdown' for systematic variations."""
    ## for UL samples trigger SFs were not available in json format
    ## falling back to HTT SFs
    if "201" in self.year_SF: 
      sf = self.sftool_trig.evaluate(eta,pt,syst)
    else:
      try:
        sf = self.sftool_trig.evaluate(self.year_SF,syst,self.wp_trig,eta,pt)
      except Exception as error:
        LOG.throw(error,"ElectronSF.getTriggerSF: Caught %r for (pt,eta,syst)=(%s,%s,%s)!"%(str(error),pt,eta,syst)+
                  "Please review EGammaPOG's recommendations and check your cuts...")
    return sf
    
  
  def getIdIsoSF(self, pt, eta, phi, syst='sf'):
    """Get SF for electron identification + reco"""
    if "2023" in self.year_SF: 
       sf_id = self.sftool_id.evaluate(self.year_SF,syst,self.wp_id,eta,pt,phi)
    else: 
       sf_id = self.sftool_id.evaluate(self.year_SF,syst,self.wp_id,eta,pt)
    if pt < 20:
       if "2023" in self.year_SF:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoBelow20",eta,pt,phi)
       else:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoBelow20",eta,pt)
    elif pt < 75:
       if "2023" in self.year_SF:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"Reco20to75",eta,pt,phi)
       elif "201" in self.year_SF:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoAbove20",eta,pt)
       else: 
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"Reco20to75",eta,pt)
    else:
       if "2023" in self.year_SF:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoAbove75",eta,pt,phi)
       elif "201" in self.year_SF:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoAbove20",eta,pt)
       else:
          sf_reco = self.sftool_id.evaluate(self.year_SF,syst,"RecoAbove75",eta,pt)

    return sf_id * sf_reco 
