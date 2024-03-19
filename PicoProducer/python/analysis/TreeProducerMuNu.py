# Author: Jacopo Malvaso (August 2022)
# Description : tree for selected  W*->muv candidates
#               in studies of high pT taus
from TauFW.PicoProducer.analysis.TreeProducerHighPT import TreeProducerHighPT

class TreeProducerMuNu(TreeProducerHighPT):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerMuNu for %r"%(filename))
    super(TreeProducerMuNu,self).__init__(filename,module,**kwargs)
    
    
    ##############
    #   MUON 1   #
    ##############
    
    self.addBranch('pt_1',       'f')
    self.addBranch('eta_1',      'f')
    self.addBranch('phi_1',      'f')
    self.addBranch('dxy_1',      'f')
    self.addBranch('dz_1',       'f')
    self.addBranch('q_1',        'i')
    self.addBranch('iso_1',      'f', title="relative isolation, pfRelIso04_all")
    self.addBranch('idMedium_1', '?')
    self.addBranch('idTight_1',  '?')
    self.addBranch('idHighPt_1', 'i')
    
    ###########
    #   GEN   #
    ###########
    if self.module.ismc:
      if self.module.dowmasswgt:
        self.addBranch('kfactor_mu',     'f',  1)
      self.addBranch('genmatch_1',     'i', -1)
      self.addBranch('idisoweight_1',  'f', 1., title="muon ID/iso efficiency SF")
    
