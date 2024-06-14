# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerETau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    super(TreeProducerETau,self).__init__(filename,module,**kwargs)
    
    
    ################
    #   ELECTRON   #
    ################
    
    self.addBranch('pt_1',                       'f', title="electron pt")
    self.addBranch('eta_1',                      'f', title="electron eta")
    self.addBranch('phi_1',                      'f', title="electron phi")
    self.addBranch('m_1',                        'f', title="electron mass")
    self.addBranch('y_1',                        'f', title="electron rapidity")
    self.addBranch('dxy_1',                      'f', title="electron dxy")
    self.addBranch('dz_1',                       'f', title="electron dz")
    self.addBranch('q_1',                        'i', title="electron charge")
    self.addBranch('iso_1',                      'f', title="pfRelIso03_all")
    self.addBranch('cutBased_1',                 '?')
    ###self.addBranch('mvaIso_1',                   'f')
    self.addBranch('mvaIso_WP80_1',              '?')
    self.addBranch('mvaIso_WP90_1',              '?')
    self.addBranch('mvanoIso_WP80_1',            '?')
    self.addBranch('mvanoIso_WP90_1',            '?')
    
    
    ###########
    #   TAU   #
    ###########
    
    self.addCommonTauBranches(tag='_2',**kwargs)
    self.addBranch('rawDeepTau2018v2p5VSe_2',    'f')
    self.addBranch('rawDeepTau2018v2p5VSmu_2',   'f')
    self.addBranch('rawDeepTau2018v2p5VSjet_2',  'f')
    self.addBranch('idDeepTau2018v2p5VSe_2',     'i')
    self.addBranch('idDeepTau2018v2p5VSmu_2',    'i')
    self.addBranch('idDeepTau2018v2p5VSjet_2',   'i')
    
    
    
    ##########
    #   MC   #
    ##########
    
    if self.module.ismc:
      self.addBranch('jpt_genmatch_2',           'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',               'i', -1)
      self.addBranch('genmatch_2',               'i', -1)
      self.addBranch('genvistaupt_2',            'f', -1)
      self.addBranch('genvistaueta_2',           'f', -9)
      self.addBranch('genvistauphi_2',           'f', -9)
      self.addBranch('gendm_2',                  'i', -1)
      self.addBranch('idisoweight_1',            'f', 1., title="electron ID/iso efficiency SF")
      self.addBranch('idweight_2',               'f', 1., title="tau ID efficiency SF")
      self.addBranch('ltfweight_2',              'f', 1., title="lepton -> tau fake rate SF")
      if self.module.dosys: # systematic variation (only for nominal tree)
        self.addBranch('idweightUp_2',           'f', 1.)
        self.addBranch('idweightDown_2',         'f', 1.)
        self.addBranch('ltfweightUp_2',          'f', 1.)
        self.addBranch('ltfweightDown_2',        'f', 1.)
    
