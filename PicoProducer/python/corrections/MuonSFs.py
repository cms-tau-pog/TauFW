# Author: Izaak Neutelings (December 2018)
# HTT: https://github.com/CMS-HTT/LeptonEfficiencies
# MuonPOG: https://gitlab.cern.ch/cms-muonPOG/muonefficiencies/-/tree/master/Run2
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonReferenceEffs2017
import os
from TauFW.PicoProducer import datadir
from ScaleFactorTool import ScaleFactor, ScaleFactorHTT
pathPOG = os.path.join(datadir,"lepton/MuonPOG/")
pathHTT = os.path.join(datadir,"lepton/HTT/Muon/")


class MuonSFs:
  
  def __init__(self, era='2017', verb=0):
    """Load histograms from files."""
    
    #eras = ['2016','2017','2018','UL2017']
    #assert era in eras, "MuonSFs: You must choose a year from: %s."%(', '.join(eras))
    self.sftool_trig = None
    self.sftool_idiso = None
    if 'UL' in era:
      if '2016' in era and 'preVFP' in era:
        # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb) # placeholder
        sftool_id         = ScaleFactor(pathPOG+"Run2016UL_preVFP/Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_ID.root","NUM_MediumID_DEN_TrackerMuons_abseta_pt",'mu_id',ptvseta=True,verb=verb)
        sftool_iso        = ScaleFactor(pathPOG+"Run2016UL_preVFP/Efficiencies_muon_generalTracks_Z_Run2016_UL_HIPM_ISO.root","NUM_TightRelIso_DEN_MediumID_abseta_pt",'mu_iso',ptvseta=False,verb=verb)
        self.sftool_idiso = sftool_id*sftool_iso
      elif '2016' in era:
        # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb) # placeholder
        sftool_id         = ScaleFactor(pathPOG+"Run2016UL_postVFP/Efficiencies_muon_generalTracks_Z_Run2016_UL_ID.root","NUM_MediumID_DEN_TrackerMuons_abseta_pt",'mu_id',ptvseta=True,verb=verb)
        sftool_iso        = ScaleFactor(pathPOG+"Run2016UL_postVFP/Efficiencies_muon_generalTracks_Z_Run2016_UL_ISO.root","NUM_TightRelIso_DEN_MediumID_abseta_pt",'mu_iso',ptvseta=False,verb=verb)
        self.sftool_idiso = sftool_id*sftool_iso
      elif '2017' in era:
        # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb) # placeholder
        sftool_id         = ScaleFactor(pathPOG+"Run2017UL/Efficiencies_muon_generalTracks_Z_Run2017_UL_ID.root","NUM_MediumID_DEN_TrackerMuons_abseta_pt",'mu_id',ptvseta=True,verb=verb)
        sftool_iso        = ScaleFactor(pathPOG+"Run2017UL/Efficiencies_muon_generalTracks_Z_Run2017_UL_ISO.root","NUM_TightRelIso_DEN_MediumID_abseta_pt",'mu_iso',ptvseta=False,verb=verb)
        self.sftool_idiso = sftool_id*sftool_iso
      elif '2018' in era:
        # https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb) # placeholder
        sftool_id         = ScaleFactor(pathPOG+"Run2018UL/Efficiencies_muon_generalTracks_Z_Run2018_UL_ID.root","NUM_MediumID_DEN_TrackerMuons_abseta_pt",'mu_id',ptvseta=True,verb=verb)
        sftool_iso        = ScaleFactor(pathPOG+"Run2018UL/Efficiencies_muon_generalTracks_Z_Run2018_UL_ISO.root","NUM_TightRelIso_DEN_MediumID_abseta_pt",'mu_iso',ptvseta=False,verb=verb)
        self.sftool_idiso = sftool_id*sftool_iso
    else:
      if era=='2016':
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2016_legacy/Muon_Run2016_legacy_IsoMu22.root",'ZMass','mu_trig',verb=verb)
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2016_legacy/Muon_Run2016_legacy_IdIso.root",'ZMass','mu_idiso',verb=verb)
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb) # placeholder
        sftool_id         = ScaleFactor(pathPOG+"Run2017UL/Efficiencies_muon_generalTracks_Z_Run2017_UL_ID.root","NUM_MediumID_DEN_TrackerMuons_abseta_pt",'mu_id',ptvseta=True,verb=verb)
        sftool_iso        = ScaleFactor(pathPOG+"Run2017UL/Efficiencies_muon_generalTracks_Z_Run2017_UL_ISO.root","NUM_TightRelIso_DEN_MediumID_abseta_pt",'mu_iso',ptvseta=False,verb=verb)
        self.sftool_idiso = sftool_id*sftool_iso
      elif era=='2017':
        #self.sftool_trig  = ScaleFactor(pathPOG+"Run2017/EfficienciesAndSF_RunBtoF_Nov17Nov2017.root","IsoMu27_PtEtaBins/abseta_pt_ratio",'mu_trig')
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Muon_IsoMu24orIsoMu27.root",'ZMass','mu_idiso',verb=verb)
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2017/Muon_IdIso_IsoLt0.15_eff_RerecoFall17.root",'ZMass','mu_idiso',verb=verb)
        #sftool_id         = ScaleFactor(pathPOG+"Run2017/RunBCDEF_SF_ID.root","NUM_MediumID_DEN_genTracks_pt_abseta",'mu_id',ptvseta=False)
        #sftool_iso        = ScaleFactor(pathPOG+"Run2017/RunBCDEF_SF_ISO.root","NUM_TightRelIso_DEN_MediumID_pt_abseta",'mu_iso',ptvseta=False)
        #self.sftool_idiso = sftool_id*sftool_iso
      elif era=='2018':
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2018/Muon_Run2018_IsoMu24orIsoMu27.root",'ZMass','mu_trig',verb=verb)
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2018/Muon_Run2018_IdIso.root") # MediumID, DB corrected iso (dR<0.4) < 0.15
        #sftool_id         = ScaleFactor(pathPOG+"Run2018/RunABCD_SF_ID.root","NUM_MediumID_DEN_genTracks_pt_abseta",'mu_id',ptvseta=False)
        #sftool_iso        = ScaleFactor(pathPOG+"Run2018/RunABCD_SF_ISO.root","NUM_TightRelIso_DEN_MediumID_pt_abseta",'mu_iso',ptvseta=False)
        #self.sftool_idiso = sftool_id*sftool_iso
    assert self.sftool_trig!=None and self.sftool_idiso!=None, "MuonSFs.__init__: Did not find muon SF tool for %r"%(era)
  
  def getTriggerSF(self, pt, eta):
    """Get SF for single muon trigger."""
    return self.sftool_trig.getSF(pt,abs(eta))
  
  def getIdIsoSF(self, pt, eta):
    """Get SF for muon identification + isolation."""
    return self.sftool_idiso.getSF(pt,abs(eta))
  
