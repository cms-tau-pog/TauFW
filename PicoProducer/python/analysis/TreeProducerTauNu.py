# Author: Jacopo Malvaso, Alexei Raspereza (August 2022)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerHighPT import TreeProducerHighPT


class TreeProducerTauNu(TreeProducerHighPT):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerTauNu for %r"%(filename))
    super(TreeProducerTauNu,self).__init__(filename,module,**kwargs)
    
        
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
    self.addBranch('rawDeepTau2017v2p1VSe_1',    'f')
    self.addBranch('rawDeepTau2017v2p1VSmu_1',   'f')
    self.addBranch('rawDeepTau2017v2p1VSjet_1',  'f')
    self.addBranch('idDecayMode_1',              '?', title="oldDecayModeFinding")
    self.addBranch('idDecayModeNewDMs_1',        '?', title="newDecayModeFinding")
    self.addBranch('idDeepTau2017v2p1VSe_1',     'i')
    self.addBranch('idDeepTau2017v2p1VSmu_1',    'i')
    self.addBranch('idDeepTau2017v2p1VSjet_1',   'i')
    self.addBranch('jpt_match_1',                'f', -1, title="pt of jet matching tau")
    self.addBranch('jpt_ratio_1',                'f', -1, title="pt(tau)/pt(jet)")    

    if self.module.ismc:
      if self.module.dowmasswgt:
        self.addBranch('kfactor_tau',            'f',  1)
      self.addBranch('idisoweight_1',            'f',  1)
      self.addBranch('jpt_genmatch_1',           'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',               'i', -1)
      self.addBranch('genvistaupt_1',            'f', -1)
      self.addBranch('genvistaueta_1',           'f', -9)
      self.addBranch('genvistauphi_1',           'f', -9)
      self.addBranch('gendm_1',                  'i', -1)

      for unc in self.module.tes_uncs:
        self.addBranch('pt_1_'+unc,         'f')
        self.addBranch('m_1_'+unc,          'f')
        self.addBranch('met_'+unc,          'f')
        self.addBranch('metphi_'+unc,       'f')
        self.addBranch('mt_1_'+unc,         'f')
        self.addBranch('metdphi_1_'+unc,    'f')
