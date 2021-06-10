# Author: Izaak Neutelings (November 2018)
# https://twiki.cern.ch/twiki/bin/view/CMS/EgammaIDRecipesRun2#Electron_efficiencies_and_scale
# https://twiki.cern.ch/twiki/bin/view/CMS/Egamma2017DataRecommendations#Efficiency_Scale_Factors
# https://github.com/CMS-HTT/LeptonEfficiencies/tree/master/Electron/
# 2018: https://hypernews.cern.ch/HyperNews/CMS/get/higgstautau/1132.html
import os
from TauFW.PicoProducer import datadir
from ScaleFactorTool import ScaleFactor, ScaleFactorHTT
pathPOG = os.path.join(datadir,"lepton/EGammaPOG/")
pathHTT = os.path.join(datadir,"lepton/HTT/Electron/")
"UL2017/egammaEffi.txt_EGM2D_MVA90noIso_UL17.root",
"UL2016_postVFP/egammaEffi.txt_Ele_wp90noiso_postVFP_EGM2D.root",
"UL2016_preVFP/egammaEffi.txt_Ele_wp90noiso_preVFP_EGM2D.root",
"UL2018/egammaEffi.txt_Ele_wp90noiso_EGM2D.root",


class ElectronSFs:
  
  def __init__(self,era='2017'):
    """Load histograms from files."""
    
    #assert era in ['2016','2017','2018'], "ElectronSFs: You must choose a year from: 2016, 2017, or 2018."
    
    self.sftool_trig = None
    self.sftool_idiso = None
    if 'UL' in era:
      # https://twiki.cern.ch/twiki/bin/view/CMS/EgammaUL2016To2018
      if '2016' in era and 'preVFP' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2016_legacy/Electron_Run2016_legacy_Ele25.root",'ZMass','ele_trig')
        self.sftool_reco  = ScaleFactor(pathPOG+"UL2016_preVFP/egammaEffi_ptAbove20.txt_EGM2D_UL2016preVFP.root",'EGamma_SF2D','ele_reco')
        self.sftool_idiso = ScaleFactor(pathPOG+"UL2016_preVFP/egammaEffi.txt_Ele_wp90noiso_preVFP_EGM2D.root",'EGamma_SF2D','ele_id')
      elif '2016' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2016_legacy/Electron_Run2016_legacy_Ele25.root",'ZMass','ele_trig')
        self.sftool_reco  = ScaleFactor(pathPOG+"UL2016_postVFP/egammaEffi_ptAbove20.txt_EGM2D_UL2016postVFP.root",'EGamma_SF2D','ele_reco')
        self.sftool_idiso = ScaleFactor(pathPOG+"UL2016_postVFP/egammaEffi.txt_Ele_wp90noiso_postVFP_EGM2D.root",'EGamma_SF2D','ele_id')
      elif '2017' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Electron_Ele35.root",'ZMass','ele_trig') #Electron_Ele32orEle35
        self.sftool_reco  = ScaleFactor(pathPOG+"UL2017/egammaEffi_ptAbove20.txt_EGM2D_UL2017.root",'EGamma_SF2D','ele_reco')
        self.sftool_idiso = ScaleFactor(pathPOG+"UL2017/egammaEffi.txt_EGM2D_MVA90noIso_UL17.root",'EGamma_SF2D','ele_id')
      elif '2018' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2018/Electron_Run2018_Ele32orEle35.root",'ZMass','ele_trig')
        self.sftool_reco  = ScaleFactor(pathPOG+"UL2018/egammaEffi_ptAbove20.txt_EGM2D_UL2018.root",'EGamma_SF2D','ele_reco')
        self.sftool_idiso = ScaleFactor(pathPOG+"UL2018/egammaEffi.txt_Ele_wp90noiso_EGM2D.root",'EGamma_SF2D','ele_id')
    else: # pre-UL
      # https://twiki.cern.ch/twiki/bin/viewauth/CMS/EgammaRunIIRecommendations
      if '2016' in era:
        #self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2016BtoH/Electron_Ele27Loose_OR_Ele25Tight_eff.root",'ZMass','ele_trig')
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2016_legacy/Electron_Run2016_legacy_Ele25.root",'ZMass','ele_trig')
        self.sftool_reco  = ScaleFactor(pathPOG+"2016/EGM2D_BtoH_GT20GeV_RecoSF_Legacy2016.root",'EGamma_SF2D','ele_reco')
        #self.sftool_idiso = ScaleFactor(pathPOG+"2016/2016LegacyReReco_ElectronMVA90noiso_Fall17V2.root",'EGamma_SF2D','ele_id')
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2016_legacy/Electron_Run2016_legacy_IdIso.root",'ZMass','ele_idiso') # MVA noIso Fall17 WP90, rho-corrected iso(dR<0.3)<0.1
      elif '2017' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2017/Electron_Ele35.root",'ZMass','ele_trig') #Electron_Ele32orEle35
        self.sftool_reco  = ScaleFactor(pathPOG+"2017/egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root",'EGamma_SF2D','ele_reco')
        #self.sftool_idiso = ScaleFactor(pathPOG+"2017/2017_ElectronMVA90noiso.root",'EGamma_SF2D','ele_id')
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2017/Electron_Run2017_IdIso.root",'ZMass','ele_idiso') # MVA noIso Fall17 WP90, rho-corrected iso(dR<0.3)<0.1
      elif '2018' in era:
        self.sftool_trig  = ScaleFactorHTT(pathHTT+"Run2018/Electron_Run2018_Ele32orEle35.root",'ZMass','ele_trig')
        self.sftool_reco  = ScaleFactor(pathPOG+"2018/egammaEffi.txt_EGM2D_updatedAll.root",'EGamma_SF2D','ele_reco')
        #self.sftool_idiso = ScaleFactor(pathPOG+"2018/2018_ElectronMVA90noiso.root",'EGamma_SF2D','ele_id')
        self.sftool_idiso = ScaleFactorHTT(pathHTT+"Run2018/Electron_Run2018_IdIso.root",'ZMass','ele_idiso') # MVA noIso Fall17 WP90, rho-corrected iso(dR<0.3)<0.1
    assert self.sftool_trig!=None and self.sftool_idiso!=None, "ElectronSFs.__init__: Did not find electron SF tool for %r"%(era)
    
    if self.sftool_reco:
      self.sftool_idiso = self.sftool_reco * self.sftool_idiso
  
  def getTriggerSF(self, pt, eta):
    """Get SF for single electron trigger."""
    return self.sftool_trig.getSF(pt,eta)
  
  def getIdIsoSF(self, pt, eta):
    """Get SF for electron identification + isolation."""
    return self.sftool_idiso.getSF(pt,eta)
  
