# Author: Alexei Raspereza (October 2022)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TreeProducerHighPT import TreeProducerHighPT


class TreeProducerWJ(TreeProducerHighPT):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print "Loading TreeProducerWJ for %r"%(filename)
    super(TreeProducerWJ,self).__init__(filename,module,**kwargs)
        
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

    ##############
    # Fake tau 2 #
    ##############

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

    self.addBranch('dphi',                       'f')

    ###########
    #   GEN   #
    ###########
    
    if self.module.ismc:
      self.addBranch('genmatch_1',     'i', -1)
      self.addBranch('genmatch_2',     'i', -1)
      self.addBranch('jpt_genmatch_2', 'f', -1, title="pt of gen jet matching fake tau")
      self.addBranch('idisoweight_1',  'f', 1., title="muon ID/iso efficiency SF")
    
