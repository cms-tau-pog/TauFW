# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerTauTau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    super(TreeProducerTauTau,self).__init__(filename,module,**kwargs)
    
    
    ############
    #   TAUS   #
    ############
    
    kwargs.pop('tag',None) # remove tag
    self.addCommonTauBranches(tag='_1',**kwargs)
    self.addCommonTauBranches(tag='_2',**kwargs)
    
    
    ##########
    #   MC   #
    ##########
    
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
      if module.dosys: # systematic variation (only for nominal tree)
        self.addBranch('idweightUp_1',           'f', 1.)
        self.addBranch('idweightUp_2',           'f', 1.)
        self.addBranch('idweightDown_1',         'f', 1.)
        self.addBranch('idweightDown_2',         'f', 1.)
        self.addBranch('ltfweightUp_1',          'f', 1.)
        self.addBranch('ltfweightUp_2',          'f', 1.)
        self.addBranch('ltfweightDown_1',        'f', 1.)
        self.addBranch('ltfweightDown_2',        'f', 1.)
    
