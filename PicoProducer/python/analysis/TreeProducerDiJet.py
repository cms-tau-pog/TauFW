# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from .TreeProducerHighPT import TreeProducerHighPT


class TreeProducerDiJet(TreeProducerHighPT):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerDiJet for %r"%(filename))
    super(TreeProducerDiJet,self).__init__(filename,module,**kwargs)
        
    ######################################
    #   TAU 2 (use same index as in WJ   #
    ######################################
    
    self.addBranch('pt_2',       'f')
    self.addBranch('eta_2',      'f')
    self.addBranch('phi_2',      'f')
    self.addBranch('m_2',        'f')
    self.addBranch('q_2',        'i')
    self.addBranch('dm_2',       'i')    
    self.addBranch('rawDeepTau2017v2p1VSe_2',    'f')
    self.addBranch('rawDeepTau2017v2p1VSmu_2',   'f')
    self.addBranch('rawDeepTau2017v2p1VSjet_2',  'f')
    self.addBranch('idDeepTau2017v2p1VSe_2',     'i')
    self.addBranch('idDeepTau2017v2p1VSmu_2',    'i')
    self.addBranch('idDeepTau2017v2p1VSjet_2',   'i')
    self.addBranch('jpt_match_2',                'f', -1, title="pt of jet matching tau")
    self.addBranch('jpt_ratio_2',                'f', -1, title="ratio of tau pt to jet pt")

    ##############
    # Jet pT     #
    ##############

    self.addBranch('jpt',       'f')
    self.addBranch('jeta',      'f')
    self.addBranch('jphi',      'f')

    self.addBranch('dphi',  'f') # angle between fake tau and jet

    ###########
    #   GEN   #
    ###########
    
    if self.module.ismc:
      self.addBranch('genmatch_2',     'i', -1)
      self.addBranch('jpt_genmatch_2', 'f', -1, title="pt of gen jet matching fake tau")
