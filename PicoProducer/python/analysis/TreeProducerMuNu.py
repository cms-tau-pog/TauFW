# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TreeProducerHighPT import TreeProducerHighPT


class TreeProducerMuNu(TreeProducerHighPT):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print "Loading TreeProducerMuNu for %r"%(filename)
    super(TreeProducerMuNu,self).__init__(filename,module,**kwargs)
    
    
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
    self.addBranch('tkRelIso_1', 'f')
    self.addBranch('idMedium_1', '?')
    self.addBranch('idTight_1',  '?')
    self.addBranch('idHighPt_1', 'i')
    self.addBranch('kfactor_mu', 'f')
    
    
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
    
