# Author: Izaak Neutelings (June 2020)
# Description: Produce generic tree for tau analysis
# Sources:
#   https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorking2016#Synchronisation
#   https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html
from ROOT import TH1D
from TreeProducerBase import TreeProducerBase


class TreeProducerTauPair(TreeProducerBase):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerTauPair,self).__init__(filename,module,**kwargs)
    print "Loading TreeProducerTauPair for %r"%(filename)
    
    # PILEUP
    self.pileup = TH1D('pileup', 'pileup', 100, 0, 100)
    
    
    #############
    #   EVENT   #
    #############
    
    self.addBranch('run',                 'i')
    self.addBranch('lumi',                'i')
    self.addBranch('evt',                 'i')
    self.addBranch('data',                '?', module.isdata)
    
    self.addBranch('npv',                 'i') # number of offline primary vertices
    self.addBranch('npv_good',            'i')
    self.addBranch('rho',                 'f') # fixedGridRhoFastjetAll
    self.addBranch('metfilter',           '?')
    
    if module.ismc:
      # https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/NPUTablesProducer.cc
      self.addBranch('npu',               'i', -1) # number of in-time pu interactions added (getPU_NumInteractions -> nPU)
      self.addBranch('npu_true',          'i', -1) # true mean number of Poisson distribution (getTrueNumInteractions -> nTrueInt)
      self.addBranch('NUP',               'i', -1) # number of partons for stitching (LHE_Njets)
    
    
    ##############
    #   WEIGHT   #
    ##############
    
    if module.ismc:
      self.addBranch('weight',            'f', 1.)
      self.addBranch('genweight',         'f', 1.)
      self.addBranch('trigweight',        'f', 1.)
      self.addBranch('puweight',          'f', 1.)
      self.addBranch('zptweight',         'f', 1.)
      self.addBranch('ttptweight',        'f', 1.)
      self.addBranch('btagweight',        'f', 1.)
      self.addBranch('prefireweight',     'f', 1.)
      self.addBranch('prefireweightUp',   'f', 1.)
      self.addBranch('prefireweightDown', 'f', 1.)
    elif module.isembed:
      self.addBranch('genweight',         'f', 1.)
      self.addBranch('trackweight',       'f', 1.)
    
    
    ############
    #   JETS   #
    ############
    
    self.addBranch('njets',               'i') # number of jets (pT > 30 GeV, |eta| < 4.7)
    self.addBranch('ncjets',              'i') # number of central jets (|eta| < 2.4)
    self.addBranch('nfjets',              'i') # number of forward jets (2.4 < |eta| < 4.7)
    self.addBranch('nbtag',               'i') # number of b tagged jets (pT > 30 GeV, |eta| < 2.7)
    
    self.addBranch('jpt_1',               'f')
    self.addBranch('jeta_1',              'f')
    self.addBranch('jphi_1',              'f')
    self.addBranch('jdeepb_1',            'f')
    self.addBranch('jpt_2',               'f')
    self.addBranch('jeta_2',              'f')
    self.addBranch('jphi_2',              'f')
    self.addBranch('jdeepb_2',            'f')
    
    self.addBranch('bpt_1',               'f')
    self.addBranch('beta_1',              'f')
    self.addBranch('bpt_2',               'f')
    self.addBranch('beta_2',              'f')
    
    ###for unc in module.jecUncLabels:
    ###  unc  = '_'+unc
    ###  unc2 = unc.replace('Total','') # shorthand
    ###  self.addBranch('njets'+unc2,         'i', arrname='njets'+unc        )
    ###  self.addBranch('njets50'+unc2,       'i', arrname='njets50'+unc      )
    ###  self.addBranch('nbtag50'+unc2,       'i', arrname='nbtag50'+unc      )
    ###  self.addBranch('nbtag50_loose'+unc2, 'i', arrname='nbtag50_loose'+unc)
    ###  self.addBranch('jpt_1'+unc2,         'f', arrname='jpt_1'+unc        )
    ###  self.addBranch('jpt_2'+unc2,         'f', arrname='jpt_2'+unc        )
    
    self.addBranch('met',                 'f')
    self.addBranch('metphi',              'f')
    ###self.addBranch('puppimet',            'f')
    ###self.addBranch('puppimetphi',         'f')
    ###self.addBranch('metsignificance',     'f')
    ###self.addBranch('mvacov00',            'f')
    ###self.addBranch('mvacov01',            'f')
    ###self.addBranch('mvacov11',            'f')
    ###for unc in module.metUncLabels:
    ###  unc = '_'+unc
    ###  unc2 = unc.replace('Total','') # shorthand
    ###  self.addBranch('met'+unc2,          'f', arrname='met'+unc,  )
    ###  self.addBranch('metphi'+unc2,       'f', arrname='metphi'+unc)
    
    if module.ismc:
      self.addBranch('genmet',            'f', -1)
      self.addBranch('genmetphi',         'f', -9)
    
    
    #############
    #   OTHER   #
    #############
    
    self.addBranch('mt_1',                'f')
    self.addBranch('mt_2',                'f')
    self.addBranch('m_vis',               'f')
    self.addBranch('pt_ll',               'f')
    self.addBranch('dR_ll',               'f')
    self.addBranch('dphi_ll',             'f')
    self.addBranch('deta_ll',             'f')
    
    self.addBranch('pzetamiss',           'f')
    self.addBranch('pzetavis',            'f')
    self.addBranch('dzeta',               'f')
    self.addBranch('chi',                 'f') # exp|y_2-y_1|
    
    ###for unc in module.metUncLabels:
    ###  unc = '_'+unc
    ###  self.addBranch('mt_1'+unc,          'f')
    ###  self.addBranch('dzeta'+unc,         'f')
    
    self.addBranch('dilepton_veto',       '?')
    self.addBranch('extraelec_veto',      '?')
    self.addBranch('extramuon_veto',      '?')
    self.addBranch('lepton_vetoes',       '?')
    self.addBranch('lepton_vetoes_notau', '?')
    
    if module.ismc:
      self.addBranch('m_moth',            'f', -1) # generator mother: Z boson, W boson, top quark, ...
      self.addBranch('pt_moth',           'f', -1)
    

