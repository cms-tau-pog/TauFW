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
from TauFW.common.python.tools.log import Logger
from TauFW.PicoProducer import datadir
from TauFW.PicoProducer.python.corrections.ScaleFactorTool import ScaleFactorHTT
from correctionlib import CorrectionSet
#pathPOG = os.path.join(datadir,"lepton/MuonPOG/") # ROOT files from MUO
pathHTT = os.path.join(datadir,"lepton/HTT/Muon/") # ROOT files from HTT
pathPOG = os.path.join(datadir,"jsonpog/POG/MUO/") # JSON files from central XPOG
pathMUO = os.path.join(datadir,"lepton/MuonPOG/") # JSON files from central XPOG
pathZpt = os.path.join(datadir,"zpt/") # JSON files from central XPOG
LOG = Logger('DYCorrections')


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
  

class DYandRecoilCorrlib:
  
  def __init__(self, era, sf_dy_ptll=None, sf_iso=None, sf_trig=None, flags=[ ], verb=0):
    """Prepare muon SFs from JSON files."""
    
    
    # SETTINGS
    fname_id = None

    #abseta      = True # use absolute eta (default in Run 2, 2022)
    sf_dy_ptll_= "DY_pTll_reweighting"
    sf_era_ = None
    sf_era = None
    sf_dy_ptll= None

    if '2022' in era or '2023' in era or '2024' in era: # Run 3
      fname_id = pathZpt + "DY_pTll_recoil_corrections.json.gz"
    
    # DEFAULTS
    if sf_dy_ptll==None:
      sf_dy_ptll = sf_dy_ptll_

    
    # CHECKS
    if not os.path.exists(fname_id):
      LOG.throw(OSError,"DYpTllCorr: fname_id=%s does not exist! Please make sure you have installed the correctionlib JSON data in %s"
                        " following the instructions in https://github.com/cms-tau-pog/TauFW/wiki/Installation#Corrections !"%(fname_id,datadir))
    
    print("Loading DYandRecoilCorrlib for %s:%r..."%(fname_id,sf_dy_ptll))
    # LOAD CORRECTIONS
    corrset = CorrectionSet.from_file(fname_id) # load JSON
    self.sftool_dyptll  = corrset[sf_dy_ptll]
    
    
  
  def getDYpTCorr(self, era, pt,order='LO', syst='nom'):

    if order not in ['LO','NLO','NNLO']:
      LOG.throw(ValueError,"DYpTllCorr.getDYpTCorr: order=%r is not supported! Supported orders: LO, NLO, NNLO"%(order))

    if re.search(r"2022([C-D]|.*pre)",era): # 2022CD (preEE)
      sf_era =  "2022preEE"
    elif re.search(r"2022([E-G]|.*post)",era): # 2022EFG (postEE)
      sf_era = "2022postEE"
    elif re.search(r"2023(C|.*pre)",era): # 2023C (preBPIX)
      sf_era = "2023preBPIX"
    elif re.search(r"2023(D|.*post)",era): # 2023D (postBPIX)
      sf_era = "2023postBPIX"
    elif '2024' in era: # 2024
      sf_era = "2022postEE"
    
    """Get SF for muon identification + isolation."""
    ###if self.abseta: # MuonPOG now consistently uses transform for eta -> abs(eta)
    ###  eta = abs(eta)
    return self.sftool_dyptll.evaluate(sf_era,order,pt,syst)
    
    

  