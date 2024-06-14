# Author: Izaak Neutelings (June 2020)
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerMuTau(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    super(TreeProducerMuTau,self).__init__(filename,module,**kwargs)
    kwargs.setdefault('study',True) # for addCommonTauBranches
    
    
    ############
    #   MUON   #
    ############
    
    self.addBranch('pt_1',       'f', title="muon pt")
    self.addBranch('eta_1',      'f', title="muon eta")
    self.addBranch('phi_1',      'f', title="muon phi")
    self.addBranch('m_1',        'f', title="muon mass")
    self.addBranch('y_1',        'f', title="muon rapidity")
    self.addBranch('dxy_1',      'f', title="muon dxy")
    self.addBranch('dz_1',       'f', title="muon dz")
    self.addBranch('q_1',        'i', title="muon charge")
    self.addBranch('iso_1',      'f', title="relative isolation, pfRelIso04_all")
    self.addBranch('tkRelIso_1', 'f')
    self.addBranch('idMedium_1', '?')
    self.addBranch('idTight_1',  '?')
    self.addBranch('idHighPt_1', 'i')
    
    
    ###########
    #   TAU   #
    ###########
    
    self.addCommonTauBranches(tag='_2',**kwargs) # adds pt, eta, idDeepTau*VS*, etc.
    
    
    ###################
    #   CORRECTIONS   #
    ###################
    
    if self.module.ismc:
      self.addBranch('jpt_genmatch_2',      'f', -1, title="pt of gen jet matching tau")
      self.addBranch('genmatch_1',          'i', -1)
      self.addBranch('genmatch_2',          'i', -1)
      self.addBranch('genvistaupt_2',       'f', -1)
      self.addBranch('genvistaueta_2',      'f', -9)
      self.addBranch('genvistauphi_2',      'f', -9)
      self.addBranch('gendm_2',             'i', -1)
      self.addBranch('idisoweight_1',       'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('idweight_2',          'f', 1., title="SF for tau ID efficiency, Tight (pT-dependent)")
      self.addBranch('idweight_dm_2',       'f', 1., title="SF for tau ID efficiency, Tight (DM-dependent)")
      self.addBranch('idweight_medium_2',   'f', 1., title="SF for tau ID efficiency, Medium")
      self.addBranch('ltfweight_2',         'f', 1., title="SF for lepton -> tau fake rate")
      if self.module.dosys: # systematic variation (only for nominal tree)
        self.addBranch('idweightUp_2',      'f', 1., title="SF for tau VSjet eff. (pT-dependent)")
        self.addBranch('idweightDown_2',    'f', 1., title="SF for tau VSjet eff. (pT-dependent)")
        self.addBranch('idweightUp_dm_2',   'f', 1., title="SF for tau VSjet eff. (DM-dependent)")
        self.addBranch('idweightDown_dm_2', 'f', 1., title="SF for tau VSjet eff. (DM-dependent)")
        self.addBranch('ltfweightUp_2',     'f', 1., title="SF for lepton -> tau fake rate (up)")
        self.addBranch('ltfweightDown_2',   'f', 1., title="SF for lepton -> tau fake rate (down)")
      if self.module.domutau:
        self.addBranch('mutaufilter',       '?', title="has tautau -> mutau, pT>18, |eta|<2.5")
    
