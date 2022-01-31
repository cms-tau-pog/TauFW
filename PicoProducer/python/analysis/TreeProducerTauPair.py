# Author: Izaak Neutelings (June 2020)
# Description: Produce generic tree for tau analysis
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from ROOT import TH1D
from TreeProducer import TreeProducer


class TreeProducerTauPair(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerTauPair,self).__init__(filename,module,**kwargs)
    #print "Loading TreeProducerTauPair for %r"%(filename)
    
    
    #############
    #   EVENT   #
    #############
    
    self.addBranch('run',                 'i')
    self.addBranch('lumi',                'i')
    self.addBranch('evt',                 'i')
    self.addBranch('data',                '?', module.isdata)
    self.setAlias("year",str(module.year)) # save as alias to storage space
    
    self.addBranch('npv',                 'i', title="number of offline primary vertices")
    self.addBranch('npv_good',            'i')
    self.addBranch('rho',                 'f', title="fixedGridRhoFastjetAll")
    self.addBranch('metfilter',           '?', title="recommended metfilters")
    
    if module.ismc:
      # https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/NPUTablesProducer.cc
      self.addBranch('npu',               'i', -1, title="number of in-time pu interactions added (getPU_NumInteractions -> nPU)")
      self.addBranch('npu_true',          'i', -1, title="true mean number of Poisson distribution (getTrueNumInteractions -> nTrueInt)")
      self.addBranch('NUP',               'i', -1, title="number of partons for stitching (LHE_Njets)")
    
    
    ##############
    #   WEIGHT   #
    ##############
    
    if module.ismc:
      self.addBranch('weight',              'f', 1., title="weight combining others (to reduce selection string length)")
      self.addBranch('genweight',           'f', 1., title="generator weight")
      self.addBranch('trigweight',          'f', 1., title="trigger SF")
      if not module.dotight:
        if module.dopdf:
          self.addBranch('npdfweight',      'i', 1., title="number of PDF weights")
          self.addBranch('pdfweight',       'f', 1., len='npdfweight', max=110, title="vector of PDF weights")
          #self.addBranch('qweight',         'f', 1., title="scale weight (Qren=1.0, Qfact=1.0)")
          #self.addBranch('qweight_0p5_0p5', 'f', 1., title="relative scale weight, Qren=0.5, Qfact=0.5")
          #self.addBranch('qweight_0p5_1p0', 'f', 1., title="relative scale weight, Qren=0.5, Qfact=1.0")
          #self.addBranch('qweight_1p0_0p5', 'f', 1., title="relative scale weight, Qren=1.0, Qfact=0.5")
          #self.addBranch('qweight_1p0_2p0', 'f', 1., title="relative scale weight, Qren=1.0, Qfact=2.0")
          #self.addBranch('qweight_2p0_1p0', 'f', 1., title="relative scale weight, Qren=2.0, Qfact=1.0")
          #self.addBranch('qweight_2p0_2p0', 'f', 1., title="relative scale weight, Qren=2.0, Qfact=2.0")
        self.addBranch('trigweightUp',      'f', 1.)
        self.addBranch('trigweightDown',    'f', 1.)
      self.addBranch('puweight',            'f', 1., title="pileup up reweighting")
      self.addBranch('zptweight',           'f', 1., title="Z pT reweighting")
      self.addBranch('ttptweight',          'f', 1., title="top pT reweighting")
      self.addBranch('btagweight',          'f', 1., title="b tagging weight")
      #if module.dosys:
      #  self.addBranch('btagweight_bc',      'f', 1., title="b tagging weight, heavy flavor")
      #  self.addBranch('btagweight_bcUp',    'f', 1., title="b tagging weight, heavy flavor up")
      #  self.addBranch('btagweight_bcDown',  'f', 1., title="b tagging weight, heavy flavor down")
      #  self.addBranch('btagweight_udsg',    'f', 1., title="b tagging weight, light flavor")
      #  self.addBranch('btagweight_udsgUp',  'f', 1., title="b tagging weight, light flavor up")
      #  self.addBranch('btagweight_udsgDown','f', 1., title="b tagging weight, light flavor down")
      self.addBranch('prefireweight',       'f', 1.)
      self.addBranch('prefireweightUp',     'f', 1.)
      self.addBranch('prefireweightDown',   'f', 1.)
    elif module.isembed:
      self.addBranch('genweight',           'f', 1., title="generator weight")
      self.addBranch('trackweight',         'f', 1.)
    
    
    ############
    #   JETS   #
    ############
    
    self.addBranch('njets',               'i', title="number of jets (pT > 30 GeV, |eta| < 4.7)")
    self.addBranch('njets50',             'i', title="number of jets (pT > 50 GeV, |eta| < 4.7)")
    self.addBranch('ncjets',              'i', title="number of central jets (pT > 30 GeV, |eta| < 2.4)")
    self.addBranch('ncjets50',            'i', title="number of central jets (pT > 50 GeV, |eta| < 2.4)")
    self.addBranch('nfjets',              'i', title="number of forward jets (pT > 30 GeV, 2.4 < |eta| < 4.7)")
    self.addBranch('nbtag',               'i', title="number of b tagged jets (pT > 30 GeV, |eta| < 2.7)")
    self.setAlias("njets30","njets")
    self.setAlias("nbtag30","nbtag")
    
    self.addBranch('jpt_1',               'f', title="pT of leading jet")
    self.addBranch('jeta_1',              'f', title="eta of leading jet")
    self.addBranch('jphi_1',              'f', title="phi of leading jet")
    self.addBranch('jdeepjet_1',          'f', title="DeepJet score of leading jet")
    self.addBranch('jpt_2',               'f', title="pT of subleading jet")
    self.addBranch('jeta_2',              'f', title="eta of subleading jet")
    self.addBranch('jphi_2',              'f', title="phi of subleading jet")
    self.addBranch('jdeepjet_2',          'f', title="DeepJet score of subleading jet")
    
    self.addBranch('bpt_1',               'f', title="pT of leading b jet")
    self.addBranch('beta_1',              'f', title="eta of leading jet")
    self.addBranch('bpt_2',               'f', title="pT of leading jet")
    self.addBranch('beta_2',              'f', title="eta of leading jet")
    
    self.addBranch('met',                 'f')
    self.addBranch('metphi',              'f')
    
    if module.ismc:
      self.addBranch('genmet',            'f', -1)
      self.addBranch('genmetphi',         'f', -9)
    
    
    #############
    #   OTHER   #
    #############
    
    self.addBranch('mt_1',                'f', title="PF transverse mass with first lepton")
    self.addBranch('mt_2',                'f', title="PF transverse mass with second lepton")
    self.addBranch('m_vis',               'f', title="invariant mass of visibile ditau system")
    self.addBranch('pt_ll',               'f', title="pT of visibile ditau system")
    self.addBranch('dR_ll',               'f', title="DeltaR of visibile ditau system")
    self.addBranch('dphi_ll',             'f', title="DeltaPhi of visibile ditau system")
    self.addBranch('deta_ll',             'f', title="DeltaEta of visibile ditau system")
    self.setAlias("m_ll","m_vis")
    self.setAlias("mvis","m_vis")
    
    self.addBranch('pzetavis',            'f', title="projection of visible ditau momentums onto bisector (zeta)")
    self.addBranch('pzetamiss',           'f', title="projection of MET onto zeta axis")
    self.addBranch('dzeta',               'f', title="pzetamiss-0.85*pzetavis")
    self.addBranch('chi',                 'f', title="exp|y_2-y_1|")
    #self.setAlias("dzeta","pzetamiss-0.85*pzetavis")
    #self.setAlias("chi","exp(abs(eta_1-eta_2))")
    self.setAlias("st","pt_1+pt_2+jpt_1")
    self.setAlias("stmet","pt_1+pt_2+jpt_1+met")
    
    self.addBranch('dilepton_veto',       '?')
    self.addBranch('extraelec_veto',      '?')
    self.addBranch('extramuon_veto',      '?')
    self.addBranch('lepton_vetoes',       '?')
    self.addBranch('lepton_vetoes_notau', '?')
    
    if module.ismc:
      if module.dotoppt:
        self.addBranch('pt_moth1',        'f', -1, title="leading top pT")
        self.addBranch('pt_moth2',        'f', -1, title="subleading top pT")
      else:
        self.addBranch('m_moth',          'f', -1, title="generator mother mass (Z boson, W boson, top quark, ...)")
        self.addBranch('pt_moth',         'f', -1, title="generator mother pT (Z boson, W boson, top quark, ...)")
    

