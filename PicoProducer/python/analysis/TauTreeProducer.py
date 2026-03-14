# Author: Andrea Cardini (Sept 2025)
# Description: Tree with just taus being stored
from ROOT import TH1D
from TauFW.PicoProducer.analysis.TreeProducer import TreeProducer


class TauTree(TreeProducer):
  
  def __init__(self, filename, module, **kwargs):
    """Class to create and prepare a custom output file & tree."""
    super(TauTree,self).__init__(filename,module,**kwargs)

    self.sumgenweights = TH1D('weightedEvents','Sum of generator weight',1,0,1)
    
    #############
    #   EVENT   #
    #############
    
    self.addBranch('run',                 'i')
    self.addBranch('lumi',                'i')
    self.addBranch('evt',                 'i')
    self.setAlias("year",str(module.year)) # save as alias to storage space
    
    if module.ismc:
      # https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/plugins/NPUTablesProducer.cc
      self.addBranch('npu',               'i', -1, title="number of in-time pu interactions added (getPU_NumInteractions -> nPU)")
      self.addBranch('npu_true',          'i', -1, title="true mean number of Poisson distribution (getTrueNumInteractions -> nTrueInt)")
      self.addBranch('NUP',               'i', -1, title="number of partons for stitching (LHE_Njets)")
      self.addBranch('HT',                'f', -1, title="LHE HT variable for stitching")
  
    ###########
    #   TAU   #
    ###########

    self.addBranch('tau_eventid',	'f')
    self.addBranch('tau_id',    	'f')
    self.addBranch('tau_dm',	        'f')
    self.addBranch('tau_pt',    	'f')
    self.addBranch('tau_eta',   	'f')
    self.addBranch('tau_phi',   	'f')
    self.addBranch('tau_mass',   	'f')
    self.addBranch('tau_charge',   	'f')
    self.addBranch('tau_gendm',  	'f')
    self.addBranch('tau_genpt',  	'f')
    self.addBranch('tau_geneta',	'f')
    self.addBranch('tau_genphi',	'f')
    self.addBranch('tau_dz',   	'f')
    self.addBranch('tau_dxy',   	'f')
    self.addBranch('tau_dxy_err',	'f')
    self.addBranch('tau_ip3d',  	'f')
    self.addBranch('tau_ip3d_err',	'f')
    self.addBranch('tau_idDecayModeNewDMs',      	'f')
    self.addBranch('tau_idDecayModeOldDMs',	'f')
    self.addBranch('tau_rawDeepTau2018v2p5VSjet',	'f')
    self.addBranch('tau_rawDeepTau2018v2p5VSmu',	'f')
    self.addBranch('tau_rawDeepTau2018v2p5VSe',  	'f')
    self.addBranch('tau_ptCorrPNet',	'f')
    self.addBranch('tau_ptCorrUParT',	'f')
    self.addBranch('tau_rawPNetVSe',	'f')
    self.addBranch('tau_rawPNetVSmu',	'f')
    self.addBranch('tau_rawPNetVSjet',	'f')
    self.addBranch('tau_rawUParTVSe',	'f')
    self.addBranch('tau_rawUParTVSmu',	'f')
    self.addBranch('tau_rawUParTVSjet',	'f')
    self.addBranch('tau_puCorr',	'f')
    self.addBranch('tau_qConfPNet',	'f')
    self.addBranch('tau_qConfUParT',	'f')
    self.addBranch('tau_nSVs',	'f')
    self.addBranch('tau_ipLengthSig',	'f')
    self.addBranch('tau_IPx',	'f')
    self.addBranch('tau_IPy',	'f')
    self.addBranch('tau_IPz',	'f')
    self.addBranch('tau_decayModePNet',	    'f')
    self.addBranch('tau_decayModeUParT',    'f')
    self.addBranch('tau_idAntiMu',	'f')
    self.addBranch('tau_leadTkDeltaEta',	'f')
    self.addBranch('tau_leadTkDeltaPhi',	'f')
    self.addBranch('tau_leadTkPtOverTauPt',	'f')
    self.addBranch('tau_rawIso',	'f')
    self.addBranch('tau_rawIsodR03',	'f')
    self.addBranch('tau_refitSVchi2',	'f')
    self.addBranch('tau_refitSVcov00',	'f')
    self.addBranch('tau_refitSVcov10',	'f')
    self.addBranch('tau_refitSVcov11',	'f')
    self.addBranch('tau_refitSVcov20',	'f')
    self.addBranch('tau_refitSVcov21',	'f')
    self.addBranch('tau_refitSVcov22',	'f')
    self.addBranch('tau_refitSVx',	'f')
    self.addBranch('tau_refitSVy',	'f')
    self.addBranch('tau_refitSVz',	'f')
    self.addBranch('tau_photonsOutsideSignalCone',	'f')
