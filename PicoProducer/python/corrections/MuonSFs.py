# Author: Izaak Neutelings (December 2018)
# HTT: https://github.com/CMS-HTT/LeptonEfficiencies
# MuonPOG: https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master/Run2
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonPOG#User_Recommendations
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonLegacy2016
# correctionlib:
#   https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration     # central XPOG repo
#   https://gitlab.cern.ch/cms-muonPOG/muonefficiencies        # early MuonPOG releases
#   https://cms-nanoaod-integration.web.cern.ch/commonJSONSFs/ # JSON contents
#   correction summary data/jsonpog/POG/MUO/*/muon_Z.json.gz   # JSON contents
#   zgrep abseta data/jsonpog/POG/MUO/*/muon_Z.json.gz         # JSON contents (check for abseta)
#   https://github.com/cms-cat/nanoAOD-tools-modules/blob/master/python/modules/muonSF.py
#   https://github.com/cms-cat/nanoAOD-tools-modules/blob/master/test/example_muonSF.py
import os, re
from TauFW.common.tools.log import Logger
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.corrections.ScaleFactorTool import ScaleFactorHTT
from correctionlib import CorrectionSet
#pathPOG = os.path.join(datadir,"lepton/MuonPOG/") # ROOT files from MUO
pathHTT = os.path.join(datadir,"lepton/HTT/Muon/") # ROOT files from HTT
pathPOG = os.path.join(datadir,"jsonpog/POG/MUO/") # JSON files from central XPOG
pathMUO = os.path.join(datadir,"lepton/MuonPOG/") # JSON files from central XPOG

LOG = Logger('MuonSF')


def getcorr(corrset,sfname,abseta=False,verb=0):
  """Help function to extract Correction object and
  check if Correction inputs are what we expect them to be."""
  keys = list(corrset.keys())
  LOG.insist(sfname in keys, "Did not find key %r in correctionset! Available keys: %r"%(sfname,keys))
  corr   = corrset[sfname]
  inputs = [i.name for i in corr._base.inputs]
  eta    = 'eta' #'abseta' if abseta else 'eta' # MuonPOG now consistently uses transform for eta -> abs(eta)
  LOG.insist(len(inputs)==3,    "Expected len(inputs)==3, but got %s... Inputs: %s"%(len(inputs),inputs))
  LOG.insist(eta in inputs[0],  "Expected %s as first input, but got %s! All inputs for %s: %s"%(eta,inputs[0],sfname,inputs))
  LOG.insist('pt' in inputs[1], "Expected pt as second input, but got %s! All inputs for %s: %s"%(inputs[1],sfname,inputs))
  return corr
  

class MuonSFs:
  
  def __init__(self, era, sf_id=None, sf_iso=None, sf_trig=None, flags=[ ], verb=0):
    """Prepare muon SFs from JSON files."""
    
    # SETTINGS
    fname_id = None
    fname_trig = None
    #abseta      = True # use absolute eta (default in Run 2, 2022)
    sf_id_   = "NUM_MediumID_DEN_TrackerMuons" # default in Run 2 + Run 3
    sf_iso_  = "NUM_TightPFIso_DEN_MediumID" # default in Run 3
    sf_trig_ = "NUM_IsoMu24_DEN_CutBasedIdTight_and_PFIsoTight" # default used in 2018 + Run 3
    if 'UL' in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016
      # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
      # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
      sf_iso_ = "NUM_TightRelIso_DEN_MediumID" # default in Run 2
      if '2016' in era and 'preVFP' in era:
        sf_trig_ = "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"
        fname_id = pathPOG+"2016preVFP_UL/muon_Z.json.gz"
      elif '2016' in era:
        sf_trig_ = "NUM_IsoMu24_or_IsoTkMu24_DEN_CutBasedIdTight_and_PFIsoTight"
        fname_id = pathPOG+"2016postVFP_UL/muon_Z.json.gz"
      elif '2017' in era:
        fname_id = pathPOG+"2018_UL/muon_Z.json.gz"
        if 'HLT_IsoMu27' in flags: # use only HLT_IsoMu27
          sf_trig_ = "NUM_IsoMu27_DEN_CutBasedIdTight_and_PFIsoTight"
        else: # default: use (HLT_IsoMu24 || HLT_IsoMu27)
          sf_trig_ = "mu_trig"
          fname_trig = pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root"
      elif '2018' in era:
        fname_id = pathPOG+"2018_UL/muon_Z.json.gz"
    else: # Run-3
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/MuonRun32022
      # https://twiki.cern.ch/twiki/bin/view/CMS/MuonRun3_2023
      if re.search(r"2022([C-D]|.*pre)",era): # 2022CD (preEE)
        fname_id = pathPOG+"2022_Summer22/muon_Z.json.gz"
      elif re.search(r"2022([E-G]|.*post)",era): # 2022EFG (postEE)
        fname_id = pathPOG+"2022_Summer22EE/muon_Z.json.gz"
      elif re.search(r"2023(C|.*pre)",era): # 2024C (preBPIX)
        fname_id = pathPOG+"2023_Summer23/muon_Z.json.gz"
        #abseta = False
      elif re.search(r"2023(D|.*post)",era): # 2024D (postBPIX)
        fname_id = pathPOG+"2023_Summer23BPix/muon_Z.json.gz"
      elif '2024' in era:
        fname_id = pathMUO + "Run2024/muon_Z_2024.json.gz"
        #abseta = False
    
    # DEFAULTS
    if sf_id==None:
      sf_id = sf_id_
    if sf_iso==None:
      sf_iso = sf_iso_
    if sf_trig==None: # default used in 2018 + Run 3
      sf_trig = sf_trig_
    
    # CHECKS
    if verb>=0:
      if fname_trig: # special exception: (HLT_IsoMu24 || HLT_IsoMu27)
        print("Loading MuonSF for era=%r, id=%r, iso=%r from %s..."%(era,sf_id,sf_id,fname_id))
      else:
        print("Loading MuonSF for era=%r, id=%r, iso=%r, trig=%r from %s..."%(era,sf_id,sf_id,sf_trig,fname_id))
    if not os.path.exists(fname_id):
      LOG.throw(OSError,"MuonSFs: fname_id=%s does not exist! Please make sure you have installed the correctionlib JSON data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"%(fname_id,datadir))
    if fname_trig and not os.path.exists(fname_trig):
      LOG.throw(OSError,"MuonSFs: fname_trig=%s does not exist! Please make sure you have installed the HTT lepton ROOT data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"%(fname_id,datadir))
    
    # LOAD CORRECTIONS
    corrset = CorrectionSet.from_file(fname_id) # load JSON
    self.sftool_id  = getcorr(corrset,sf_id, verb=verb)
    self.sftool_iso = getcorr(corrset,sf_iso,verb=verb)
    if fname_trig: # special exception: load ROOT file for (HLT_IsoMu24 || HLT_IsoMu27)
      print("Loading MuonSF for era=%r, trig=%r from %s..."%(era,sf_trig,fname_trig))
      self.sftool_trig = ScaleFactorHTT(fname_trig,'ZMass',sf_trig,verb=verb) # HTT ROOT
    elif '2024' in era:
      self.sftool_trig = 1.0 # no trigger SF in 2024 at the moment
    else: # load correctionlib JSON: HLT_IsoMu24, HLT_IsoMu27, etc.
      self.sftool_trig = corrset[sf_trig] # correctionlib JSON
    
  
  def getTriggerSF(self, pt, eta, syst=None):
    """Get SF for single muon trigger.
    Use syst='systup', 'systdown' for systematic variations."""
    ###if self.abseta: # MuonPOG now consistently uses transform for eta -> abs(eta)
    ###  eta = abs(eta)
    try:
      sf = self.sftool_trig.evaluate(eta,pt,'nominal')
      if syst: # systematic variations: 'syst', 'stat', ...
        unc = self.sftool_id.evaluate(eta,pt,syst)
        sf = (sf,sf+unc,sf-unc)
    except Exception as error:
      LOG.throw(error,"MuonSF.getTriggerSF: Caught %r for (pt,eta,syst)=(%s,%s,%s)!"%(str(error),pt,eta,syst)+
                "Please review MuonPOG's recommendations and check your cuts...")
    return sf
    
  
  def getIdIsoSF(self, pt, eta, syst='nominal'):
    """Get SF for muon identification + isolation."""
    ###if self.abseta: # MuonPOG now consistently uses transform for eta -> abs(eta)
    ###  eta = abs(eta)
    return self.sftool_id.evaluate(eta,pt,syst)*self.sftool_iso.evaluate(eta,pt,syst)
    
  
  def getIdSF(self, pt, eta, syst=None):
    """Get SF for muon identification."""
    sf = self.sftool_id.evaluate(eta,pt,'nominal')
    if syst: # systematic variations: syst = 'syst', 'stat', ...
      unc = self.sftool_id.evaluate(eta,pt,syst)
      return (sf,sf+unc,sf-unc) # (nominal, up, down)
    return sf # nominal
    
  
  def getIsoSF(self, pt, eta, syst=None):
    """Get SF for muon isolation."""
    sf = self.sftool_iso.evaluate(eta,pt,'nominal')
    if syst: # systematic variations: syst = 'syst', 'stat', ...
      unc = self.sftool_iso.evaluate(eta,pt,syst)
      return (sf,sf+unc,sf-unc) # (nominal, up, down)
    return sf # nominal
    
  