# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair
import ROOT


class TreeProducerMuTau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerMuTau for %r"%(filename))
    super(TreeProducerMuTau,self).__init__(filename,module,**kwargs)
    
    # TRIGGER BRANCHES
    self.addBranch('HLT_IsoMu24', '?', False, title="Trigger branch for HLT_IsoMu24")
    self.addBranch('HLT_IsoMu24_eta2p1', '?', False, title="Trigger branch for HLT_IsoMu24_eta2p1")

    # PNet trigger branches
    self.addBranch('HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Loose_eta2p3_CrossL1', '?', False, title="Trigger branch (PNet, MuTau Loose)")
    self.addBranch('HLT_IsoMu24_eta2p1_PNetTauhPFJet30_Medium_L2NN_eta2p3_CrossL1', '?', False, title="Trigger branch (PNet, MuTau Medium)")
    self.addBranch('HLT_IsoMu24_eta2p1_PNetTauhPFJet26_L2NN_eta2p3_CrossL1', '?', False, title="Trigger branch (PNet, DiTau+Jet)")
    self.addBranch('HLT_IsoMu20_eta2p1_PNetTauhPFJet27_Tight_eta2p3_CrossL1', '?', False, title="Trigger branch (PNet, MuTau Tight)")
    self.addBranch('HLT_IsoMu24_eta2p1_PNetTauhPFJet45_L2NN_eta2p3_CrossL1', '?', False, title="Trigger branch (PNet, VBF SingleTau)")
    self.addBranch('HLT_IsoMu24_eta2p1_PNetTauhPFJet20_eta2p2_SingleL1', '?', False, title="Trigger branch (PNet, VBF DiTau)")

    # DeepTau trigger branches
    self.addBranch('HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1', '?', False, title="Trigger branch (DeepTau, MuTau Loose)")
    self.addBranch('HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS35_L2NN_eta2p1_CrossL1', '?', False, title="Trigger branch (DeepTau, DiTau)")
    self.addBranch('HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS30_L2NN_eta2p1_CrossL1', '?', False, title="Trigger branch (DeepTau, DiTau+Jet)")
    self.addBranch('HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS45_L2NN_eta2p1_CrossL1', '?', False, title="Trigger branch (DeepTau, VBF SingleTau)")
    self.addBranch('HLT_IsoMu24_eta2p1_MediumDeepTauPFTauHPS20_eta2p1_SingleL1', '?', False, title="Trigger branch (DeepTau, VBF DiTau)")

    #L1 branches
    self.addBranch('L1_mutau',        '?', False, title="L1: Mu18er2p1+Tau24/26 (mutau group)")
    self.addBranch('L1_etau',         '?', False, title="L1: Mu18er2p1+Tau24/26 (etau group)")
    self.addBranch('L1_ditau',        '?', False, title="L1: Mu22er2p1+IsoTau32/34/36 or Mu22er2p1+Tau70")
    self.addBranch('L1_ditaujet',     '?', False, title="L1: Mu18er2p1+Tau24/26 and Tau26+Jet55/70")
    self.addBranch('L1_singletau',    '?', False, title="L1: Mu22er2p1+IsoTau40")
    self.addBranch('L1_vbfsingletau', '?', False, title="L1: Mu22er2p1+IsoTau32/34/36 or Mu22er2p1+Tau70 (VBF single tau)")
    self.addBranch('L1_vbfditau',     '?', False, title="L1: SingleMu22 (VBF ditau placeholder)")

    ###############
    #   TRIGOBJ   #
    ###############
    # DeepTau trigger bits
    self.addBranch('trig_match_DeepTau_MuTau', '?', False)
    self.addBranch('trig_match_DeepTau_DiTau', '?', False)
    self.addBranch('trig_match_DeepTau_DiTauJet', '?', False)
    self.addBranch('trig_match_DeepTau_ETau', '?', False)
    self.addBranch('trig_match_DeepTau_VBFSingleTau', '?', False)
    self.addBranch('trig_match_DeepTau_VBFDiTau', '?', False)

    # PNet trigger bits
    self.addBranch('trig_match_PNet_MuTau_Loose', '?', False)
    self.addBranch('trig_match_PNet_MuTau_Medium', '?', False)
    self.addBranch('trig_match_PNet_MuTau_Tight', '?', False)
    self.addBranch('trig_match_PNet_DiTau_Loose', '?', False)
    self.addBranch('trig_match_PNet_DiTau_Medium', '?', False)
    self.addBranch('trig_match_PNet_DiTau_Tight', '?', False)
    self.addBranch('trig_match_PNet_DiTauJet', '?', False)
    self.addBranch('trig_match_PNet_ETau_Loose', '?', False)
    self.addBranch('trig_match_PNet_ETau_Medium', '?', False)
    self.addBranch('trig_match_PNet_ETau_Tight', '?', False)
    self.addBranch('trig_match_PNet_VBFSingleTau', '?', False)
    self.addBranch('trig_match_PNet_VBFDiTau', '?', False)

    self.addBranch('pass_tag', '?', False)
    self.addBranch('pass_probe', '?', False)
    self.addBranch('trig_match_single_muon', '?', False)
    self.addBranch('trig_obj_15', '?', False)
    self.addBranch('trig_obj_13', '?', False)
    self.addBranch('dR_mu', '?', False)

    self.addBranch('PV_npvsGood', 'i', 0, title="Number of good reconstructed primary vertices")

    #### MET FILTER ######
    self.addBranch('Flag_METFilters', 'bool')
    self.addBranch('Flag_goodVertices', 'bool')
    self.addBranch('Flag_globalSuperTightHalo2016Filter', 'bool')
    self.addBranch('Flag_HBHENoiseFilter', 'bool')
    self.addBranch('Flag_HBHENoiseIsoFilter', 'bool')
    self.addBranch('Flag_EcalDeadCellTriggerPrimitiveFilter', 'bool')
    self.addBranch('Flag_BadPFMuonFilter', 'bool')
    self.addBranch('Flag_BadPFMuonDzFilter', 'bool')
    self.addBranch('Flag_ecalBadCalibFilter', 'bool')
    self.addBranch('Flag_eeBadScFilter', 'bool')

    ############
    #   MUON   #
    ############
    
    self.addBranch('pt_1',       'f')
    self.addBranch('eta_1',      'f')
    self.addBranch('phi_1',      'f')
    self.addBranch('m_1',        'f')
    self.addBranch('y_1',        'f')
    self.addBranch('dxy_1',      'f')
    self.addBranch('dz_1',       'f')
    self.addBranch('q_1',        'i')
    self.addBranch('iso_1',      'f', title="relative isolation, pfRelIso04_all")
    self.addBranch('tkRelIso_1', 'f')
    self.addBranch('idMedium_1', '?')
    self.addBranch('idTight_1',  '?')
    self.addBranch('idHighPt_1', 'i')
    
    
    ###########
    #   TAU   #
    ###########
    
    self.addBranch('pt_2',                       'f')
    self.addBranch('eta_2',                      'f')
    self.addBranch('phi_2',                      'f')
    self.addBranch('m_2',                        'f')
    self.addBranch('y_2',                        'f')
    self.addBranch('dxy_2',                      'f')
    self.addBranch('dz_2',                       'f')
    self.addBranch('q_2',                        'i')
    self.addBranch('dm_2',                       'i')
    self.addBranch('iso_2',                      'f', title="rawIso")
    self.addBranch('idiso_2',                    'i', title="rawIso WPs")
    #self.addBranch('rawAntiEle_2',               'f') # not available anymore in nanoAODv9
    #self.addBranch('rawMVAoldDM2017v2_2',        'f')
    #self.addBranch('rawMVAnewDM2017v2_2',        'f')
    self.addBranch('rawDeepTau2017v2p1VSe_2',    'f')
    self.addBranch('rawDeepTau2017v2p1VSmu_2',   'f')
    self.addBranch('rawDeepTau2017v2p1VSjet_2',  'f')

    self.addBranch('rawDeepTau2018v2p5VSe_2',    'f')
    self.addBranch('rawDeepTau2018v2p5VSmu_2',   'f')
    self.addBranch('rawDeepTau2018v2p5VSjet_2',  'f')


    #self.addBranch('idAntiEle_2',                'i')
    #self.addBranch('idAntiMu_2',                 'i')
    self.addBranch('idDecayMode_2',              '?', title="oldDecayModeFinding")
    self.addBranch('idDecayModeNewDMs_2',        '?', title="newDecayModeFinding")
    #self.addBranch('idMVAoldDM2017v2_2',         'i')
    #self.addBranch('idMVAnewDM2017v2_2',         'i')
    self.addBranch('idDeepTau2017v2p1VSe_2',     'i')
    self.addBranch('idDeepTau2017v2p1VSmu_2',    'i')
    self.addBranch('idDeepTau2017v2p1VSjet_2',   'i')

    self.addBranch('idDeepTau2018v2p5VSe_2',     'i')
    self.addBranch('idDeepTau2018v2p5VSmu_2',    'i')
    self.addBranch('idDeepTau2018v2p5VSjet_2',   'i')


    self.addBranch('leadTkPtOverTauPt_2',        'f')
    self.addBranch('chargedIso_2',               'f')
    self.addBranch('neutralIso_2',               'f')
    self.addBranch('photonsOutsideSignalCone_2', 'f')
    self.addBranch('puCorr_2',                   'f')
    self.addBranch('jpt_match_2',                'f', -1, title="pt of jet matching tau")
    
    if self.module.ismc:
      self.addBranch('jpt_genmatch_2',      'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',          'i', -1)
      self.addBranch('genmatch_2',          'i', -1)
      self.addBranch('genvistaupt_2',       'f', -1)
      self.addBranch('genvistaueta_2',      'f', -9)
      self.addBranch('genvistauphi_2',      'f', -9)
      self.addBranch('gendm_2',             'i', -1)
      self.addBranch('idisoweight_1',       'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('idweight_2',          'f', 1., title="tau ID efficiency SF, Tight")
      self.addBranch('idweight_dm_2',       'f', 1., title="tau ID efficiency SF, Tight, DM-dependent")
      self.addBranch('idweight_medium_2',   'f', 1., title="tau ID efficiency SF, Medium")
      self.addBranch('ltfweight_2',         'f', 1., title="lepton -> tau fake rate SF")
      if self.module.dosys: # systematic variation (only for nominal tree)
        self.addBranch('idweightUp_2',      'f', 1.)
        self.addBranch('idweightDown_2',    'f', 1.)
        self.addBranch('idweightUp_dm_2',   'f', 1.)
        self.addBranch('idweightDown_dm_2', 'f', 1.)
        self.addBranch('ltfweightUp_2',     'f', 1.)
        self.addBranch('ltfweightDown_2',   'f', 1.)
      if self.module.domutau:
        self.addBranch('mutaufilter',       '?', title="has tautau -> mutau, pT>18, |eta|<2.5")

    for name, dtype, default, title in [
      ('extramuon_veto', '?', False, "Extra muon veto flag"),
      ('extraelec_veto', '?', False, "Extra electron veto flag"),
      ('dilepton_veto', '?', False, "Dilepton veto flag"),
      ('lepton_vetoes', '?', False, "Any lepton veto flag (muon, electron, dilepton)"),
      ('lepton_vetoes_notau', '?', False, "Any lepton veto excluding tau"),
    ]:
      if not hasattr(self, name):
        self.addBranch(name, dtype, default, title=title)

    for name, dtype, default, title in [
      ('genweight',     'f', 1.0, "Event weight from generator"),
      ('puweight',      'f', 1.0, "Pileup reweighting"),
      ('trigweight',    'f', 1.0, "Trigger efficiency scale factor"),
      ('idisoweight_2', 'f', 1.0, "Tau ID+ISO SF (if used)"),
      ('trackweight',   'f', 1.0, "Tracking weight for embedded samples"),
      ('weight',        'f', 1.0, "Total event weight"),
    ]:
      if not hasattr(self, name):
        self.addBranch(name, dtype, default, title=title)