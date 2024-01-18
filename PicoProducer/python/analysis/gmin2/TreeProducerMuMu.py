# Author: Izaak Neutelings (May 2023)
# Description: Simple module to pre-select mumu events for g-2
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
#from ROOT import TH1D, TH2D
from TauFW.PicoProducer.analysis.TreeProducerTauPair import TreeProducerTauPair


class TreeProducerMuMu(TreeProducerTauPair):
  """Class to create and prepare a custom output file & tree."""
  
  def __init__(self, filename, module, **kwargs):
    print("Loading TreeProducerMuMu for %r"%(filename))
    super(TreeProducerMuMu,self).__init__(filename,module,**kwargs)
    
    
    ##################
    #   HISTOGRAMS   #
    ##################
    # ...
    
    
    ##############
    #   MUON 1   #
    ##############
    
    self.addBranch('pt_1',       'f')
    self.addBranch('eta_1',      'f')
    self.addBranch('phi_1',      'f')
    #self.addBranch('m_1',        'f')
    #self.addBranch('y_1',        'f')
    self.addBranch('dxy_1',      'f')
    self.addBranch('dz_1',       'f')
    self.addBranch('q_1',        'i')
    self.addBranch('iso_1',      'f', title="Relative isolation, pfRelIso04_all")
    #self.addBranch('tkRelIso_1', 'f')
    #self.addBranch('idMedium_1', '?')
    #self.addBranch('idTight_1',  '?')
    #self.addBranch('idHighPt_1', 'i')
    
    
    ##############
    #   MUON 2   #
    ##############
    
    self.addBranch('pt_2',       'f')
    self.addBranch('eta_2',      'f')
    self.addBranch('phi_2',      'f')
    #self.addBranch('m_2',        'f')
    #self.addBranch('y_2',        'f')
    self.addBranch('dxy_2',      'f')
    self.addBranch('dz_2',       'f')
    self.addBranch('q_2',        'i')
    self.addBranch('iso_2',      'f', title="Relative isolation, pfRelIso04_all")
    #self.addBranch('tkRelIso_2', 'f')
    #self.addBranch('idMedium_2', '?')
    #self.addBranch('idTight_2',  '?')
    #self.addBranch('idHighPt_2', 'i')
    
    
    ##############
    ####   TAU   #
    ##############
    ###
    ###self.addBranch('pt_3',                     'f')
    ###self.addBranch('eta_3',                    'f')
    ###self.addBranch('m_3',                      'f')
    ###self.addBranch('q_3',                      'f')
    ###self.addBranch('dm_3',                     'f')
    ###self.addBranch('iso_3',                    'i', title="rawIso")
    ###self.addBranch('idiso_3',                  'i', title="rawIso WPs")
    ####self.addBranch('idAntiEle_3',              'i')
    ####self.addBranch('idAntiMu_3',               'i')
    ####self.addBranch('idMVAoldDM2017v2_3',       'i')
    ####self.addBranch('idMVAnewDM2017v2_3',       'i')
    ###self.addBranch('idDeepTau2017v2p1VSe_3',   'i')
    ###self.addBranch('idDeepTau2017v2p1VSmu_3',  'i')
    ###self.addBranch('idDeepTau2017v2p1VSjet_3', 'i')
    ###self.addBranch('idDeepTau2018v2p5VSe_3',   'i')
    ###self.addBranch('idDeepTau2018v2p5VSmu_3',  'i')
    ###self.addBranch('idDeepTau2018v2p5VSjet_3', 'i')
    ###self.addBranch('jpt_match_3',              'i', title="pt of jet matching tau")
    
    
    #############
    #   EVENT   #
    #############
    
    self.addBranch('pv_z',              'f', title="PV z position [cm]");
    self.addBranch('bs_z',              'f', title="Beam spot z position [cm]");
    self.addBranch('bs_sigma',          'f', title="Beam spot z width [cm]");
    self.addBranch('bs_sigmaErr',       'f', title="Beam spot z width error [cm]");
    #self.addBranch('bs_zErr',           'f', title="Beam spot z position error [cm]");
    if module.ismc:
      self.addBranch('pv_z_gen',        'f', title="PV z position (gen-level) [cm]");
      ###self.setAlias('bs_z_raw',"0.02488") # set in endJob instead
      ###self.setAlias('bs_sigma_raw',"3.5")
    self.setAlias('bs_sigmaUp',  'bs_sigma+bs_sigmaErr')
    self.setAlias('bs_sigmaDown','bs_sigma-bs_sigmaErr')
    self.setAlias('aco',"(1-abs(dphi_ll)/3.14159265)")
    self.setAlias('z_mumu',"pv_z+0.5*dz_1+0.5*dz_2")
    
    
    #############
    #   TRACK   #
    #############
    
    # TRACK COUNTING
    nmax = 51 # maximum number of tracks
    self.addBranch('ntrack',               'i',    title="Number of tracks within dz < 0.05 cm window around dilepton vertex");
    self.addBranch('ntrack_1',             'int8', title="Number of tracks matched to leading lepton");
    self.addBranch('ntrack_2',             'int8', title="Number of tracks matched to subleading lepton");
    self.addBranch('ntrack_hs',            'i',    title="Number of tracks from hard scattering");
    self.addBranch('ntrack_pu',            'i',    title="Number of tracks from BS-corrected PU");
    self.addBranch('ntrack_pu_raw',        'i',    title="Number of tracks from uncorrected PU");
    self.addBranch('ntrack_pu_0p1',        'int8', len=200, title="Number of tracks in 0.1 cm windows between z = -10 cm [i=0] to 10 cm [i=200] (BS-corrected)");
    if module.ismc: # to save disk space
      self.addBranch('ntrack_puUp',        'i',    title="Number of tracks from BS-corrected PU, up");
      self.addBranch('ntrack_puDown',      'i',    title="Number of tracks from BS-corrected PU, down");
      self.addBranch('ntrack_pu_0p1Up',    'int8', len=200, title="Number of tracks in 0.1 cm windows between z = -10 cm [i=0] to 10 cm [i=200] (BS-corrected, up)");
      self.addBranch('ntrack_pu_0p1Down',  'int8', len=200, title="Number of tracks in 0.1 cm windows between z = -10 cm [i=0] to 10 cm [i=200] (BS-corrected, down)");
      self.addBranch('ntrack_pu_0p1_raw',  'int8', len=200, title="Number of tracks in 0.1 cm windows between z = -10 cm [i=0] to 10 cm [i=200] (uncorrected)");
      self.setAlias('ntrack_allUp',  "ntrack_hs+ntrack_puUp")
      self.setAlias('ntrack_allDown',"ntrack_hs+ntrack_puDown")
    self.setAlias('ntrack_all',      "ntrack_hs+ntrack_pu")
    self.setAlias('ntrack_all_raw',  "ntrack_hs+ntrack_pu_raw")
    
    # TRACK KINEMATICS
    self.addBranch('track_pt',             'f', len='ntrack', max=nmax);
    ###self.addBranch('track_eta',            'f', len='ntrack', max=nmax);
    ####self.addBranch('track_phi',            'f', len='ntrack', max=nmax);
    ###self.addBranch('track_dz',             'f', len='ntrack', max=nmax);
    ####self.addBranch('track_dxy',            'f', len='ntrack', max=nmax);
    ###self.addBranch('track_dR_1',           'f', len='ntrack', max=nmax);
    ###self.addBranch('track_dR_2',           'f', len='ntrack', max=nmax);
    ###self.addBranch('track_charge',         'i', len='ntrack', max=nmax);
    self.addBranch('track_ishs',           '?', len='ntrack', max=nmax);
    ####self.addBranch('track_lostInnerHits',  'i', len='ntrack', max=nmax);
    ####self.addBranch('track_trackHighPurity','i', len='ntrack', max=nmax);
    
    
    ###########
    #   GEN   #
    ###########
    
    if self.module.ismc:
      ###self.addBranch('genmatch_1',     'i', -1)
      ###self.addBranch('genmatch_2',     'i', -1)
      ###self.addBranch('genmatch_3',     'i', -1)
      ###self.addBranch('jpt_genmatch_3', 'i', -1, title="pt of gen jet matching tau")
      ###self.addBranch('genPartFlav_3',  'i', -1)
      self.addBranch('idisoweight_1',  'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('idisoweight_2',  'f', 1., title="muon ID/iso efficiency SF")
      self.addBranch('putrackweight',  'f', 1.)
      self.addBranch('hstrackweight',  'f', 1.)
      self.addBranch('acoweight',      'f', 1.)
    
