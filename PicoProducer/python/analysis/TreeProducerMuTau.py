# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TreeProducerTauPair import TreeProducerTauPair


class TreeProducerMuTau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print "Loading TreeProducerMuTau for %r"%(filename)
    super(TreeProducerMuTau,self).__init__(filename,module,**kwargs)
    
    
    ############
    #   MUON   #
    ############
    
    self.addBranch('pt_1',                       'f')
    self.addBranch('eta_1',                      'f')
    self.addBranch('phi_1',                      'f')
    self.addBranch('m_1',                        'f')
    self.addBranch('y_1',                        'f')
    self.addBranch('dxy_1',                      'f')
    self.addBranch('dz_1',                       'f')
    self.addBranch('q_1',                        'i')
    self.addBranch('iso_1',                      'f', title="pfRelIso04_all")
    
    
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
    self.addBranch('rawAntiEle_2',               'f')
    self.addBranch('rawMVAoldDM2017v2_2',        'f')
    self.addBranch('rawMVAnewDM2017v2_2',        'f')
    self.addBranch('rawDeepTau2017v2p1VSe_2',    'f')
    self.addBranch('rawDeepTau2017v2p1VSmu_2',   'f')
    self.addBranch('rawDeepTau2017v2p1VSjet_2',  'f')
    self.addBranch('idAntiEle_2',                'i')
    self.addBranch('idAntiMu_2',                 'i')
    self.addBranch('idDecayMode_2',              '?', title="oldDecayModeFinding")
    self.addBranch('idDecayModeNewDMs_2',        '?', title="newDecayModeFinding")
    self.addBranch('idMVAoldDM2017v2_2',         'i')
    self.addBranch('idMVAnewDM2017v2_2',         'i')
    self.addBranch('idDeepTau2017v2p1VSe_2',     'i')
    self.addBranch('idDeepTau2017v2p1VSmu_2',    'i')
    self.addBranch('idDeepTau2017v2p1VSjet_2',   'i')
    self.addBranch('leadTkPtOverTauPt_2',        'f')
    self.addBranch('chargedIso_2',               'f')
    self.addBranch('neutralIso_2',               'f')
    self.addBranch('photonsOutsideSignalCone_2', 'f')
    self.addBranch('puCorr_2',                   'f')
    self.addBranch('jpt_match_2',                'f', -1, title="pt of jet matching tau")
    
    if self.module.ismc:
      self.addBranch('jpt_genmatch_2',           'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',               'i', -1)
      self.addBranch('genmatch_2',               'i', -1)
      self.addBranch('genvistaupt_2',            'f', -1)
      self.addBranch('genvistaueta_2',           'f', -9)
      self.addBranch('genvistauphi_2',           'f', -9)
      self.addBranch('gendm_2',                  'i', -1)
      self.addBranch('idisoweight_1',            'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('idweight_2',               'f', 1., title="tau ID efficiency SF, Tight")
      self.addBranch('idweight_dm_2',            'f', 1., title="tau ID efficiency SF, Tight, DM-dependent")
      self.addBranch('idweight_medium_2',        'f', 1., title="tau ID efficiency SF, Medium")
      self.addBranch('ltfweight_2',              'f', 1., title="lepton -> tau fake rate SF")
      if not module.dotight:
        self.addBranch('idweightUp_2',           'f', 1.)
        self.addBranch('idweightDown_2',         'f', 1.)
        self.addBranch('idweightUp_dm_2',        'f', 1.)
        self.addBranch('idweightDown_dm_2',      'f', 1.)
        self.addBranch('ltfweightUp_2',          'f', 1.)
        self.addBranch('ltfweightDown_2',        'f', 1.)
      if self.module.dozpt:
        self.addBranch('mutaufilter',            '?', title="has tautau -> mutau, pT>18, |eta|<2.5")
    
