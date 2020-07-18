# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TreeProducerTauPair import TreeProducerTauPair


class TreeProducerTauTau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print "Loading TreeProducerTauTau for %r"%(filename)
    super(TreeProducerTauTau,self).__init__(filename,module,**kwargs)
    
        
    #############
    #   TAU 1   #
    #############
    
    self.addBranch('pt_1',                       'f')
    self.addBranch('eta_1',                      'f')
    self.addBranch('phi_1',                      'f')
    self.addBranch('m_1',                        'f')
    self.addBranch('y_1',                        'f')
    self.addBranch('dxy_1',                      'f')
    self.addBranch('dz_1',                       'f')
    self.addBranch('q_1',                        'i')
    self.addBranch('dm_1',                       'i')
    self.addBranch('iso_1',                      'f', title="rawIso")
    self.addBranch('idiso_1',                    'i', title="rawIso WPs")
    self.addBranch('rawDeepTau2017v2p1VSe_1',    'f')
    self.addBranch('rawDeepTau2017v2p1VSmu_1',   'f')
    self.addBranch('rawDeepTau2017v2p1VSjet_1',  'f')
    self.addBranch('idAntiEle_1',                'i')
    self.addBranch('idAntiMu_1',                 'i')
    self.addBranch('idDecayMode_1',              '?', title="oldDecayModeFinding")
    self.addBranch('idDecayModeNewDMs_1',        '?', title="newDecayModeFinding")
    self.addBranch('idMVAoldDM2017v2_1',         'i')
    self.addBranch('idMVAnewDM2017v2_1',         'i')
    self.addBranch('idDeepTau2017v2p1VSe_1',     'i')
    self.addBranch('idDeepTau2017v2p1VSmu_1',    'i')
    self.addBranch('idDeepTau2017v2p1VSjet_1',   'i')
    self.addBranch('leadTkPtOverTauPt_1',        'f')
    self.addBranch('chargedIso_1',               'f')
    self.addBranch('neutralIso_1',               'f')
    self.addBranch('photonsOutsideSignalCone_1', 'f')
    self.addBranch('puCorr_1',                   'f')
    self.addBranch('jpt_match_1',                'f', -1, title="pt of jet matching tau")
    
        
    #############
    #   TAU 2   #
    #############
    
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
      self.addBranch('jpt_genmatch_1',           'f', -1, title="pt of gen jet matching tau")
      self.addBranch('jpt_genmatch_2',           'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',               'i', -1)
      self.addBranch('genmatch_2',               'i', -1)
      self.addBranch('genvistaupt_1',            'f', -1)
      self.addBranch('genvistaupt_2',            'f', -1)
      self.addBranch('genvistaueta_1',           'f', -9)
      self.addBranch('genvistaueta_2',           'f', -9)
      self.addBranch('genvistauphi_1',           'f', -9)
      self.addBranch('genvistauphi_2',           'f', -9)
      self.addBranch('gendm_1',                  'i', -1)
      self.addBranch('gendm_2',                  'i', -1)
      self.addBranch('trigweight_tight',         'f', 1.)
      self.addBranch('idweight_1',               'f', 1., title="tau ID efficiency SF")
      self.addBranch('idweight_2',               'f', 1., title="tau ID efficiency SF")
      self.addBranch('idweight_tight_1',         'f', 1., title="tau ID efficiency SF")
      self.addBranch('idweight_tight_2',         'f', 1., title="tau ID efficiency SF")
      self.addBranch('ltfweight_1',              'f', 1., title="lepton -> tau fake rate SF")
      self.addBranch('ltfweight_2',              'f', 1., title="lepton -> tau fake rate SF")
      if not module.dotight:
        self.addBranch('idweightUp_1',           'f', 1.)
        self.addBranch('idweightUp_2',           'f', 1.)
        self.addBranch('idweightDown_1',         'f', 1.)
        self.addBranch('idweightDown_2',         'f', 1.)
        self.addBranch('ltfweightUp_1',          'f', 1.)
        self.addBranch('ltfweightUp_2',          'f', 1.)
        self.addBranch('ltfweightDown_1',        'f', 1.)
        self.addBranch('ltfweightDown_2',        'f', 1.)
    
