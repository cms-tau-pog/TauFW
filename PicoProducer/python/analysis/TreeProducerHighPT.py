# Author : Andrea Cardini, Jacopo Malvaso (August 2022)
# Description: base tree class for high pT tau analysis
from ROOT import TH1D
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer

class TreeProducerHighPT(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TreeProducerHighPT,self).__init__(filename,module,**kwargs)
    print("Loading TreeProducerHighPT for %r"%(filename))
    
    #### SCALE VARIATIONS SUMS OF WEIGHTS
    ###if not module.dotight:
    ###  #self.h_pdfweight = TH1D('pdfweight', 'PDF weight variations', 150, 0, 150)
    ###  self.h_muweight = TH1D('muweight', 'Sum of muR & muF scale variation weights', 10, 0, 10)
    ###  self.h_muweight_genw = TH1D('muweight_genweighted', 'Sum of muR & muF scale variation weights (weighted)', 10, 0, 10)
    ###  for i, label in enumerate(['0p5_0p5','0p5_1p0','0p5_2p0','1p0_0p5','1p0_1p0',
    ###                             '1p0_2p0','2p0_0p5','2p0_1p0','2p0_2p0',]):
    ###    self.h_muweight.GetXaxis().SetBinLabel(i+1,label)
    ###    self.h_muweight_genw.GetXaxis().SetBinLabel(i+1,label)

    self.sumgenweights = TH1D('weightedEvents','Sum of generator weight',1,0,1)
    self.sumgenw2 = TH1D('weighted2Events','Sum of generator w2',1,0,1)
    
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
    self.addBranch('mettrigger',          '?', False, title="Met trigger")
    self.addBranch('tautrigger1',         '?', False, title="Single Tau Trigger 1")
    self.addBranch('tautrigger2',         '?', False, title="Single Tau Trigger 2")
    
    if module.ismc:
      # https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/NPUTablesProducer.cc
      self.addBranch('npu',               'i', -1, title="number of in-time pu interactions added (getPU_NumInteractions -> nPU)")
      self.addBranch('npu_true',          'i', -1, title="true mean number of Poisson distribution (getTrueNumInteractions -> nTrueInt)")
      self.addBranch('NUP',               'i', -1, title="number of partons for stitching (LHE_Njets)")
      self.addBranch('NUP_LO',            'i', -1, title="number of partons at LO")
      self.addBranch('NUP_NLO',           'i', -1, title="number of partons at NLO")
      self.addBranch('HT',                'f', -1, title="LHE HT variable for stitching")
    
    ##############
    #   WEIGHT   #
    ##############
 
    self.addBranch('weight',              'f', 1., title="weight combining others (to reduce selection string length)") # will have weight also for data
    if module.ismc:
      self.addBranch('genweight',           'f', 1., title="generator weight")
      self.addBranch('trigweight',          'f', 1., title="trigger SF")
      if not module.dotight:
        if module.dopdf:
          self.addBranch('npdfweight',      'i', 1., title="number of PDF weights")
          self.addBranch('pdfweight',       'f', 1., len='npdfweight', max=110, title="vector of PDF weights")
      self.addBranch('puweight',            'f', 1., title="pileup up reweighting")
      self.addBranch('zptweight',           'f', 1., title="Z pT reweighting")
      self.addBranch('ttptweight',          'f', 1., title="top pT reweighting")
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
    self.setAlias("njets30","njets")

    ####################
    
    self.addBranch('met',                 'f')
    self.addBranch('metphi',              'f')
    self.addBranch('metnomu',             'f') # ETmis w/o muons needed for MET trigger
    self.addBranch('mhtnomu',             'f') # MHT w/o muons needed for MET trigger
    self.addBranch('mt_1',                'f', title="PF transverse mass with first lepton")
    self.addBranch('metdphi_1',           'f', title="Delta(phi) between MET and first lepton")
    self.addBranch('mt_jet_1',            'f', title="PF transverse mass with first lepton-jet")
    self.addBranch('metdphi_jet_1',       'f', title="Delta(phi) between MET and first lepton-jet")

    ##################
    # MET variations #
    ##################
    if module.dojecsys:
      for unc in module.metUncLabels:
        self.addBranch('met_'+unc,           'f')
        self.addBranch('metphi_'+unc,        'f')
        self.addBranch('metdphi_1_'+unc,     'f')
        self.addBranch('mt_1_'+unc,          'f')
        self.addBranch('mt_jet_1_'+unc,      'f')
        self.addBranch('metdphi_jet_1_'+unc, 'f')

    if module.ismc:
      self.addBranch('genmet',            'f', -1)
      self.addBranch('genmetphi',         'f', -9)
    
    #############
    #   VETOS   #
    #############
    
    self.addBranch('extraelec_veto',      '?')
    self.addBranch('extramuon_veto',      '?')
    self.addBranch('extratau_veto',       '?')
    
    if module.ismc:
      if module.dotoppt:
        self.addBranch('pt_moth1',        'f', -1, title="leading top pT")
        self.addBranch('pt_moth2',        'f', -1, title="subleading top pT")
      else:
        self.addBranch('m_moth',          'f', -1, title="generator mother mass (Z boson, W boson, top quark, ...)")
        self.addBranch('pt_moth',         'f', -1, title="generator mother pT (Z boson, W boson, top quark, ...)")
    

