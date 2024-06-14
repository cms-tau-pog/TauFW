# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerEE(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    super(TreeProducerEE,self).__init__(filename,module,**kwargs)
    
    
    ########################
    #   LEADING ELECTRON   #
    ########################
    
    self.addBranch('pt_1',                     'f', title="leading electron pt")
    self.addBranch('eta_1',                    'f', title="leading electron eta")
    self.addBranch('phi_1',                    'f', title="leading electron phi")
    self.addBranch('m_1',                      'f', title="leading electron mass")
    self.addBranch('y_1',                      'f', title="leading electron rapidity")
    self.addBranch('dxy_1',                    'f', title="leading electron dxy")
    self.addBranch('dz_1',                     'f', title="leading electron dz")
    self.addBranch('q_1',                      'i', title="leading electron charge")
    self.addBranch('iso_1',                    'f', title="relative isolation, pfRelIso03_all")
    self.addBranch('cutBased_1',               '?')
    ###self.addBranch('mvaFall17Iso_1',           'f')
    self.addBranch('mvaIso_WP80_1',            '?')
    self.addBranch('mvaIso_WP90_1',            '?')
    self.addBranch('mvanoIso_WP80_1',          '?')
    self.addBranch('mvanoIso_WP90_1',          '?')
    
    
    ###########################
    #   SUBLEADING ELECTRON   #
    ###########################
    
    self.addBranch('pt_2',                     'f', title="subleading electron pt")
    self.addBranch('eta_2',                    'f', title="subleading electron eta")
    self.addBranch('phi_2',                    'f', title="subleading electron phi")
    self.addBranch('m_2',                      'f', title="subleading electron mass")
    self.addBranch('y_2',                      'f', title="subleading electron rapidity")
    self.addBranch('dxy_2',                    'f', title="subleading electron dxy")
    self.addBranch('dz_2',                     'f', title="subleading electron dz")
    self.addBranch('q_2',                      'i', title="subleading electron charge")
    self.addBranch('iso_2',                    'f', title="relative isolation, pfRelIso03_all")
    self.addBranch('cutBased_2',               '?')
    ###self.addBranch('mvaFall17Iso_2',           'f')
    self.addBranch('mvaIso_WP80_2',            '?')
    self.addBranch('mvaIso_WP90_2',            '?')
    self.addBranch('mvanoIso_WP80_2',          '?')
    self.addBranch('mvanoIso_WP90_2',          '?')
    
    
    ###########
    #   GEN   #
    ###########
    
    if self.module.ismc:
      self.addBranch('genmatch_1',             'i', -1)
      self.addBranch('genmatch_2',             'i', -1)
      self.addBranch('idisoweight_1',          'f', 1., title="leading electron ID/iso efficiency SF")
      self.addBranch('idisoweight_2',          'f', 1., title="subleading electron ID/iso efficiency SF")
    
