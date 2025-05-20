# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerMuMu(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerMuMu for %r"%(filename))
    super(TreeProducerMuMu,self).__init__(filename,module,**kwargs)
    
    
    ##############
    #   MUON 1   #
    ##############
    
    self.addBranch('pt_1',       'f')
    self.addBranch('eta_1',      'f')
    self.addBranch('phi_1',      'f')
    self.addBranch('m_1',        'f')
    self.addBranch('y_1',        'f')
    self.addBranch('dxy_1',      'f')
    self.addBranch('dz_1',       'f')
    self.addBranch('q_1',        'i')
    self.addBranch('iso_1',      'f', title="relative isolation, pfRelIso04_all")
    #self.addBranch('tkRelIso_1', 'f')
    self.addBranch('idMedium_1', '?')
    self.addBranch('idTight_1',  '?')
    self.addBranch('idHighPt_1', 'i')
    
    
    ##############
    #   MUON 2   #
    ##############
    
    self.addBranch('pt_2',       'f')
    self.addBranch('eta_2',      'f')
    self.addBranch('phi_2',      'f')
    self.addBranch('m_2',        'f')
    self.addBranch('y_2',        'f')
    self.addBranch('dxy_2',      'f')
    self.addBranch('dz_2',       'f')
    self.addBranch('q_2',        'i')
    self.addBranch('iso_2',      'f', title="relative isolation, pfRelIso04_all")
    #self.addBranch('tkRelIso_2', 'f')
    self.addBranch('idMedium_2', '?')
    self.addBranch('idTight_2',  '?')
    self.addBranch('idHighPt_2', 'i')
    
    
    ###########
    #   TAU   #
    ###########
    
    self.addBranch('pt_3',                     'f')
    self.addBranch('eta_3',                    'f')
    self.addBranch('m_3',                      'f')
    self.addBranch('q_3',                      'f')
    self.addBranch('dm_3',                     'f')
    self.addBranch('iso_3',                    'i', title="rawIso")
    self.addBranch('idiso_3',                  'i', title="rawIso WPs")
    #self.addBranch('idAntiEle_3',              'i')
    #self.addBranch('idAntiMu_3',               'i')
    #self.addBranch('idMVAoldDM2017v2_3',       'i')
    #self.addBranch('idMVAnewDM2017v2_3',       'i')
    self.addBranch('idDeepTau2017v2p1VSe_3',   'i')
    self.addBranch('idDeepTau2017v2p1VSmu_3',  'i')
    self.addBranch('idDeepTau2017v2p1VSjet_3', 'i')
    self.addBranch('idDeepTau2018v2p5VSe_3',   'i')
    self.addBranch('idDeepTau2018v2p5VSmu_3',  'i')
    self.addBranch('idDeepTau2018v2p5VSjet_3', 'i')

    self.addBranch('rawDeepTau2018v2p5VSe_3',    'f')
    self.addBranch('rawDeepTau2018v2p5VSmu_3',   'f')
    self.addBranch('rawDeepTau2018v2p5VSjet_3',  'f')

    self.addBranch('rawPNetVSe_3',               'f')
    self.addBranch('rawPNetVSjet_3',             'f')
    self.addBranch('rawPNetVSmu_3',              'f')

    self.addBranch('decayModePNet_3',             'i')

    self.addBranch('probDM0PNet_3',               'f')
    self.addBranch('probDM1PNet_3',               'f')
    self.addBranch('probDM2PNet_3',               'f')
    self.addBranch('probDM10PNet_3',               'f')
    self.addBranch('probDM11PNet_3',               'f')

    self.addBranch('ptCorrPNet_3',                'f')
    self.addBranch('qConfPNet_3',                'f')


    self.addBranch('jpt_match_3',              'i', title="pt of jet matching tau")
    

    self.addBranch('decayModeUParT_3',              'i')
    self.addBranch('rawUParTVSe_3',                   'f')
    self.addBranch('rawUParTVSmu_3',                   'f')
    self.addBranch('rawUParTVSjet_3',                   'f')
    self.addBranch('probDM0UParT_3',               'f')
    self.addBranch('probDM1UParT_3',               'f')
    self.addBranch('probDM2UParT_3',               'f')
    self.addBranch('probDM10UParT_3',               'f')
    self.addBranch('probDM11UParT_3',               'f')
    self.addBranch('ptCorrUParT_3',                'f')
    self.addBranch('qConfUParT_3',                'f')

    ###########
    #   GEN   #
    ###########
    
    if self.module.ismc:
      self.addBranch('genmatch_1',     'i', -1)
      self.addBranch('genmatch_2',     'i', -1)
      self.addBranch('genmatch_3',     'i', -1)
      self.addBranch('jpt_genmatch_3', 'i', -1, title="pt of gen jet matching tau")
      self.addBranch('genPartFlav_3',  'i', -1)
      self.addBranch('idisoweight_1',  'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('idisoweight_2',  'f', 1., title="muon ID/iso efficiency SF")
    
