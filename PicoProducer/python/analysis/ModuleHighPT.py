# Author: Jacopo Malvaso (August 2022)
# Description: Base class for high pT tau analysis
from ROOT import TFile, TTree, RDataFrame
import sys, re
import math
import numpy as np
from math import sqrt, exp, cos
from ROOT import TLorentzVector, TVector3
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.PicoProducer.corrections.PileupTool import *
from TauFW.PicoProducer.corrections.RecoilCorrectionTool import *
#from TauFW.PicoProducer.corrections.PreFireTool import *
from TauFW.PicoProducer.corrections.BTagTool import BTagWeightTool, BTagWPs
from TauFW.common.tools.log import header
from TauFW.PicoProducer.analysis.utils import ensurebranches, redirectbranch, deltaPhi, getmet, getmetfilters, correctmet, getlepvetoes, deltaPhiLV, deltaPhi
__metaclass__ = type # to use super() with subclasses from CommonProducer
tauSFVersion  = { 2016: '2016Legacy', 2017: '2017ReReco', 2018: '2018ReReco', 2022: '2022'}


class ModuleHighPT(Module):
  """Base class the channels of an analysis with muon and neutrino: for munu, taunu, jetjet."""
  
  def __init__(self, fname, **kwargs):
    print(header(self.__class__.__name__))
    
    # SETTINGS
    self.filename   = fname # output file name
    self.dtype      = kwargs.get('dtype',    'data'         )
    self.ismc       = self.dtype=='mc'
    self.isdata     = self.dtype=='data' or self.dtype=='embed'
    self.isembed    = self.dtype=='embed'
    self.channel    = kwargs.get('channel',  'none'         ) # channel name
    self.year       = kwargs.get('year',     2022           ) # integer, e.g. 2017, 2018
    self.era        = kwargs.get('era',      '2022'         ) # string, e.g. '2017', 'UL2017'
    self.ees        = kwargs.get('ees',      1.0            ) # electron energy scale
    self.tes        = kwargs.get('tes',      None           ) # tau energy scale; if None, recommended values are applied
    self.tessys     = kwargs.get('tessys',   None           ) # vary TES: 'Up' or 'Down'
    self.fes        = kwargs.get('fes',      None           ) # electron-tau-fake energy scale: None, 'Up' or 'Down' (override with 'ltf=1')
    self.ltf        = kwargs.get('ltf',      None           ) # lepton-tau-fake energy scale
    self.jtf        = kwargs.get('jtf',      1.0            ) or 1.0 # jet-tau-fake energy scale
    self.tauwp      = kwargs.get('tauwp',    1              ) # minimum DeepTau WP, e.g. 1 = VVVLoose, etc.
    self.dotoppt    = kwargs.get('toppt',    'TT' in fname  ) # top pT reweighting
    self.dozpt      = kwargs.get('zpt',      'DY' in fname  ) # Z pT reweighting
    self.dopdf      = kwargs.get('dopdf',    False          ) and self.ismc # store PDF & scale weights
    self.dorecoil   = kwargs.get('recoil',   False          ) and self.ismc # recoil corrections #('DY' in name or re.search(r"W\d?Jets",name)) and self.year==2016) # and self.year==2016 
    self.dosys      = self.tessys in [None,''] and self.ltf in [1,None] and self.jtf in [1,None] # include systematic variations of weight
    self.dosys      = kwargs.get('sys',      self.dosys     ) # store fewer branches to save disk space
    self.dotight    = self.tes not in [1,None] or not self.dosys # tighten pre-selection to store fewer events
    self.dotight    = kwargs.get('tight',    self.dotight   ) # store fewer events to save disk space
    self.dojec      = kwargs.get('jec',      True           ) and self.ismc #and self.year==2016 #False
    self.dojecsys   = kwargs.get('jecsys',   self.dojec     ) and self.ismc and self.dosys #and self.dojec #and False
    self.useT1      = kwargs.get('useT1',    False          ) # MET T1
    self.verbosity  = kwargs.get('verb',     0              ) # verbosity
    self.dowmasswgt = kwargs.get('dowmasswgt',  False       ) # doing w mass reweighting
    self.jetCutPt   = 30
    self.isUL       = 'UL' in self.era
    if self.year==2018 or self.year==2017:
      self.trigtau1 = lambda e: e.HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1_1pr
      self.trigtau2 = lambda e: e.HLT_MediumChargedIsoPFTau180HighPtRelaxedIso_Trk50_eta2p1
    elif self.year==2016:
      self.trigtau1 = lambda e: e.HLT_VLooseIsoPFTau120_Trk50_eta2p1
      self.trigtau2 = lambda e: e.HLT_VLooseIsoPFTau140_Trk50_eta2p1
    else:
      self.trigtau1 = lambda e: e.HLT_LooseDeepTauPFTauHPS180_L2NN_eta2p1
      self.trigtau2 = lambda e: e.HLT_LooseDeepTauPFTauHPS180_L2NN_eta2p1

    if '2016' in self.era:
      self.year = 2016
    elif '2017' in self.era:
      self.year = 2017
    elif '2018' in self.era:
      self.year = 2018
      

    self.histnameZpt = 'zptmass_weight'
    if self.year == 2022:
      self.histnameZpt = 'zptmass_histo'

    assert self.year in [2016,2017,2018,2022], "Did not recognize year %s! Please choose from 2016, 2017, 2018, 2022"%self.year
    assert self.dtype in ['mc','data','embed'], "Did not recognize data type '%s'! Please choose from 'mc', 'data' and 'embed'."%self.dtype
    
    # YEAR-DEPENDENT IDs
#    self.met        = getmet(self.era,"nom" if self.dojec else "",useT1=self.useT1,verb=self.verbosity)
    self.filter     = getmetfilters(self.era,self.isdata,verb=self.verbosity)
    
    # CORRECTIONS
    self.jecUncLabels = [ ]
    self.metUncLabels = [ ]
    if self.ismc:
      self.puTool     = PileupWeightTool(era=self.era,sample=self.filename,verb=self.verbosity)
      if self.dozpt:
        self.zptTool  = ZptCorrectionTool(era=self.era,histname=self.histnameZpt)
      if self.dojecsys:
      #  self.jecUncLabels = [ u+v for u in ['jer','jesTotal'] for v in ['Down','Up']]
        self.metUncLabels = [ u+v for u in ['JER','JES','Unclustered'] for v in ['Down','Up']]
      if self.isUL and self.tes==None:
        self.tes = 1.0 # placeholder
    
  
  def beginJob(self):
    """Before processing any events or files."""
    print("")
    print(">>> %-12s = %r"%('filename',  self.filename))
    print(">>> %-12s = %s"%('year',      self.year))
    print(">>> %-12s = %r"%('dtype',     self.dtype))
    print(">>> %-12s = %r"%('channel',   self.channel))
    print(">>> %-12s = %s"%('ismc',      self.ismc))
    print(">>> %-12s = %s"%('isdata',    self.isdata))
    print(">>> %-12s = %s"%('isembed',   self.isembed))
    if self.channel.count('tau')>0:
      print(">>> %-12s = %s"%('tes',     self.tes))
      print(">>> %-12s = %r"%('tessys',  self.tessys))
      print(">>> %-12s = %r"%('fes',     self.fes))
      print(">>> %-12s = %s"%('ltf',     self.ltf))
      print(">>> %-12s = %s"%('jtf',     self.jtf))
    print(">>> %-12s = %s"%('dotoppt',   self.dotoppt))
    print(">>> %-12s = %s"%('dopdf',     self.dopdf))
    print(">>> %-12s = %s"%('dozpt',     self.dozpt))
    print(">>> %-12s = %s"%('dojec',     self.dojec))
    print(">>> %-12s = %s"%('dojecsys',  self.dojecsys))
    print(">>> %-12s = %s"%('dosys',     self.dosys))
    print(">>> %-12s = %s"%('dotight',   self.dotight))
    print(">>> %-12s = %s"%('useT1',     self.useT1))
    print(">>> %-12s = %s"%('jetCutPt',  self.jetCutPt))
    print(">>> %-12s = %s"%('dowmasswgt',self.dowmasswgt))
    
  
  def endJob(self):
    """Wrap up after running on all events and files"""
#    if self.ismc:
#      self.btagTool.setDir(self.out.outfile,'btag')
    self.out.endJob()
    
  
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    """Before processing a new file."""
    sys.stdout.flush()
    branches = [
      ('Electron_mvaFall17V2Iso',        'Electron_mvaFall17Iso'        ),
      ('Electron_mvaFall17V2Iso_WPL',    'Electron_mvaFall17Iso_WPL'    ),
      ('Electron_mvaFall17V2Iso_WP80',   'Electron_mvaFall17Iso_WP80'   ),
      ('Electron_mvaFall17V2Iso_WP90',   'Electron_mvaFall17Iso_WP90'   ),
      ('Electron_mvaFall17V2noIso_WPL',  'Electron_mvaFall17noIso_WPL'  ),
      ('Electron_mvaFall17V2noIso_WP80', 'Electron_mvaFall17noIso_WP80' ),
      ('Electron_mvaFall17V2noIso_WP90', 'Electron_mvaFall17noIso_WP90' ),
      ('Flag_ecalBadCalibFilterV2',      True                           ),
      ('Tau_idDecayMode',                [True]*32                      ), # not available anymore in nanoAODv9
      ('Tau_idDecayModeNewDMs',          [True]*32                      ), # not available anymore in nanoAODv9
      #('Tau_rawAntiEle',                 [0.]*30                        ), #  # not available anymore in nanoAODv9
      #('Tau_rawMVAoldDM2017v2',          [0.]*30                        ), # not available anymore in nanoAODv9
      #('Tau_rawMVAnewDM2017v2',          [0.]*30                        ), # not available anymore in nanoAODv9
    ]
    if self.year==2016:
      branches += [
        ('HLT_IsoMu22_eta2p1',   False ),
        ('HLT_IsoTkMu22_eta2p1', False ),
        ('HLT_IsoMu24',          False ),
        ('HLT_IsoTkMu24',        False ),
      ]
    ensurebranches(inputTree,branches) # make sure Event object has these branches

    #if self.ismc and re.search(r"W[1-5]?JetsToLNu",inputFile.GetName()): # fix genweight bug in Summer19
    #redirectbranch(1.,"genWeight") # replace Events.genWeight with single 1.0 value
    
    # save number of weights

    if self.isdata:
      total_w = 0.
      total_w2 = 0.
      for tree_name in [ 'Events']:
        df = RDataFrame(tree_name, inputFile)
        df = df.Define('genWeightD', '1.0')
        df = df.Define('genWeightD2', 'std::pow(genWeightD, 2)')
        w = df.Sum('genWeightD')
        w2 = df.Sum('genWeightD2')
        total_w += w.GetValue()
        total_w2 += w2.GetValue()
      self.out.sumgenweights.Fill(0.5,total_w)
      self.out.sumgenw2.Fill(0.5,total_w2)
    else:
      if self.era=='UL2017':
        runTree = inputFile.Get('Runs')
        genEventSumw = np.zeros(1,dtype='d')
        runTree.SetBranchAddress("genEventSumw",genEventSumw)
        nentries = runTree.GetEntries()
        for entry in range(0,nentries):
          runTree.GetEntry(entry)
          self.out.sumgenweights.Fill(0.5,genEventSumw[0])
      else:
        total_w = 0.
        total_w2 = 0.
        for tree_name in [ 'Events', 'EventsNotSelected' ]:
          df = RDataFrame(tree_name, inputFile)
          df = df.Define('genWeightD', 'std::copysign<double>(1., genWeight)')
          df = df.Define('genWeightD2', 'std::pow(genWeightD, 2)')
          w = df.Sum('genWeightD')
          w2 = df.Sum('genWeightD2')
          total_w += w.GetValue()
          total_w2 += w2.GetValue()
        self.out.sumgenweights.Fill(0.5,total_w)
        self.out.sumgenw2.Fill(0.5,total_w2)
  
  def fillhists(self,event):
    """Help function to fill common histograms (cutflow etc.) before any cuts."""
    self.out.cutflow.fill('none')
    if self.isdata:
      self.out.cutflow.fill('weight',1.)
      if event.PV_npvs>0:
        self.out.cutflow.fill('weight_no0PU',1.)
      else:
        return False
    else:
      self.out.cutflow.fill('weight',event.genWeight)
      self.out.pileup.Fill(event.Pileup_nTrueInt)
      #if self.dosys and event.nLHEScaleWeight>0:
      #idxs = [(0,0),(1,5),(2,10),(3,15),(4,20),(5,24),(6,29),(7,34),(8,39)] if event.nLHEScaleWeight>40 else\
      #       [(0,0),(1,1),(2,2),(3,3),(5,4),(6,5),(7,6),(8,7)] if event.nLHEScaleWeight==8 else\
      #       [(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)]
      #if event.nLHEScaleWeight==8:
      #  self.out.h_muweight.Fill(4,event.LHEWeight_originalXWGTUP)
      #  self.out.h_muweight_genw.Fill(4,event.LHEWeight_originalXWGTUP*event.genWeight)
      #for ibin, idx in idxs: # Ren. & fact. scale
      #  if idx>=event.nLHEScaleWeight: break
      #  self.out.h_muweight.Fill(ibin,event.LHEWeight_originalXWGTUP*event.LHEScaleWeight[idx])
      #  self.out.h_muweight_genw.Fill(ibin,event.LHEWeight_originalXWGTUP*event.LHEScaleWeight[idx]*event.genWeight)
      if event.Pileup_nTrueInt>0:
        self.out.cutflow.fill('weight_no0PU',event.genWeight)
      else: # bug in pre-UL 2017 caused small fraction of events with nPU<=0
        return False
    return True
    
  
  def fillEventBranches(self,event):
    """Help function to fill branches of common event variables."""
    
    # EVENT
    self.out.evt[0]             = event.event & 0xffffffffffffffff
    self.out.data[0]            = self.isdata
    self.out.run[0]             = event.run
    self.out.lumi[0]            = event.luminosityBlock
    self.out.npv[0]             = event.PV_npvs
    self.out.npv_good[0]        = event.PV_npvsGood
    self.out.metfilter[0]       = self.filter(event)
    try:
      self.out.mettrigger[0]    = event.HLT_PFMETNoMu120_PFMHTNoMu120_IDTight or event.HLT_PFMETNoMu130_PFMHTNoMu130_IDTight or event.HLT_PFMETNoMu140_PFMHTNoMu140_IDTight
    except RuntimeError:
      self.out.mettrigger[0]    = False

    try:
      self.out.tautrigger1[0] = self.trigtau1(event)
      self.out.tautrigger2[0] = self.trigtau2(event)
    except RuntimeError:
      self.out.tautrigger1[0] = False
      self.out.tautrigger2[0] = False
    
    if self.ismc:
      ###self.out.ngentauhads[0]   = ngentauhads
      ###self.out.ngentaus[0]      = ngentaus
      self.out.genmet[0]        = event.GenMET_pt
      self.out.genmetphi[0]     = event.GenMET_phi
      self.out.npu[0]           = event.Pileup_nPU
      self.out.npu_true[0]      = event.Pileup_nTrueInt
      try:
        self.out.NUP[0]         = event.LHE_Njets
      except RuntimeError:
        self.out.NUP[0]         = -1
      try:
        self.out.HT[0]          = event.LHE_HT
      except RuntimeError:
        self.out.HT[0]          = -1
      try:
        self.out.NUP_LO[0]      = event.LHE_NpLO
      except RuntimeError:
        self.out.NUP_LO[0]      = -1
      try:
        self.out.NUP_NLO[0]     = event.LHE_NpNLO
      except RuntimeError:
        self.out.NUP_NLO[0]     = -1
  
    elif self.isembed:
      self.out.isdata[0]        = False

  def taujetmatch(self,event,tau,ismc):
    jpt_match    = -1
    jpt_genmatch = -1
    jeta_match   = -9999
    jeta_genmatch = -9999
    if tau.jetIdx>=0:
      jpt_match = event.Jet_pt[tau.jetIdx]
      jeta_match = event.Jet_eta[tau.jetIdx]
      if ismc:
        if event.Jet_genJetIdx[tau.jetIdx]>=0:
          jpt_genmatch = event.GenJet_pt[event.Jet_genJetIdx[tau.jetIdx]]
          jeta_genmatch = event.GenJet_eta[event.Jet_genJetIdx[tau.jetIdx]]
    return jpt_match, jeta_match, jpt_genmatch, jeta_genmatch
      
  def met_sys(self,event,unc):
    metsys_pt = getattr(event,"PuppiMET_pt"+unc)
    metsys_phi = getattr(event,"PuppiMET_phi"+unc)
    metsys = TLorentzVector();
    metsys.SetXYZT(metsys_pt*math.cos(metsys_phi),metsys_pt*math.sin(metsys_phi),0.,metsys_pt)
    return metsys

  def fillJetMETBranches(self,event,leptons,lep1): 
    """Help function to select jets after removing overlap with tau decay candidates,
    and fill the jet and met variable branches."""

    #######################
    # sum up muon momenta
    #######################
    ht_muons = TLorentzVector()
    ht_muons.SetXYZT(0,0,0,0)
    for muon in Collection(event,'Muon'):
      if muon.pt<10: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if not muon.looseId: continue
      if muon.pfRelIso04_all>0.3: continue
      ht_muons += muon.p4()

    
    # MET NOMINAL AND VARIATIONS
    met_pt     = event.PuppiMET_pt
    met_phi    = event.PuppiMET_phi
    met        = TLorentzVector()
    met.SetXYZT(met_pt*math.cos(met_phi),met_pt*math.sin(met_phi),0.,met_pt)
    
    met_vars = {}
    if self.dojecsys:
      for unc in self.metUncLabels:
        met_vars[unc]  = self.met_sys(event,unc) # TLVs
    
    lep1.tlv = lep1.p4()
    # PROPAGATE TES/LTF/JTF shift to MET (assume shift is already applied to object)
    if self.ismc and 'tau' in self.channel:
      if hasattr(lep1,'es') and lep1.es!=1:
        dp = lep1.tlv*(1.-1./lep1.es) # assume shift is already applied
        correctmet(met,dp)
        
    # print(">>> fillMETAndDiLeptonBranches: Correcting MET for es=%.3f, pt=%.3f, dpt=%.3f, gm=%d"%(lep2.es,lep2.pt,dp.Pt(),lep2.genPartFlav))
        
    lep1 = lep1.tlv # continue with TLorentzVector
    
    # MET
    self.out.met[0]       = met.Pt()
    self.out.metphi[0]    = met.Phi()
    dphi = deltaPhiLV(lep1,met)
    self.out.mt_1[0]      = sqrt( 2*lep1.Pt()*met.Pt()*(1-cos(dphi) ) ) 
    self.out.metdphi_1[0] = dphi

    # MET no muon
    metNoMu = met + ht_muons
    self.out.metnomu[0] = metNoMu.Pt()
    
    # MET SYSTEMATICS
    for unc in met_vars:
      getattr(self.out,"met_"+unc)[0]    = met_vars[unc].Pt()
      getattr(self.out,"metphi_"+unc)[0] = met_vars[unc].Phi()
      dphi = deltaPhiLV(lep1,met_vars[unc])
      getattr(self.out,"mt_1_"+unc)[0]   = sqrt( 2 * lep1.Pt() * met_vars[unc].Pt() * ( 1 - cos(dphi) ) )
      getattr(self.out,'metdphi_1_'+unc)[0] = dphi


    # COUNTERS
    jets           = [ ]
    nfjets, ncjets = 0, 0
    njets50, ncjets50  = 0, 0

    ht_jets = TLorentzVector()
    ht_jets.SetXYZT(0,0,0,0)
    # SELECT JET, remove overlap with selected objects
    lep_jet = lep1
    drMin = 0.4
    for jet in Collection(event,'Jet'):
      if abs(jet.eta)>5.0: continue
      if (jet.pt<10): continue
      ht_jets = ht_jets + jet.p4() 
      if abs(jet.eta)>4.7: continue
      overlap = False
      if jet.DeltaR(lep1)<drMin:
        lep_jet = jet.p4()
        drMin = jet.DeltaR(lep1)
      for lepton in leptons:
        if jet.DeltaR(lepton)<0.5: 
          overlap = True
          break
      if overlap: continue

      if (self.era=='2017'or self.era=='2018') and (jet.jetId<2): continue # Tight
      elif (self.era=='2016') and (jet.jetId < 1): continue #Loose
      
      # PT CUT
      if jet.pt<self.jetCutPt: continue
      jets.append(jet)
      
      # COUNT JETS PT>50
      if jet.pt>50:
        njets50 += 1
      # COUNT FORWARD/CENTRAL
      if abs(jet.eta)>2.4:
        nfjets += 1
      else:
        ncjets += 1
        if jet.pt>50:
          ncjets50 += 1
      
    mht = ht_jets - ht_muons

    #    print('lepjet',lep_jet.Pt(),'lep',lep1.Pt())

    dphi_j = deltaPhiLV(lep_jet,met)
    self.out.mt_jet_1[0]      = sqrt( 2*lep_jet.Pt()*met.Pt()*(1-cos(dphi_j) ) ) 
    self.out.metdphi_jet_1[0] = dphi_j
    # MET SYSTEMATICS
    for unc in met_vars:
      dphi_j = deltaPhiLV(lep_jet,met_vars[unc])
      getattr(self.out,"mt_jet_1_"+unc)[0]   = sqrt( 2 * lep_jet.Pt() * met_vars[unc].Pt() * ( 1 - cos(dphi_j) ) )
      getattr(self.out,'metdphi_jet_1_'+unc)[0] = dphi_j

    
    self.out.njets[0]         = len(jets)
    self.out.njets50[0]       = njets50
    self.out.nfjets[0]        = nfjets
    self.out.ncjets[0]        = ncjets
    self.out.ncjets50[0]      = ncjets50
    self.out.mhtnomu[0]       = mht.Pt()
    
    ## FILL JET VARIATION BRANCHES (Not available in NanoAOD v10)
    #    if self.dojecsys:
    #      for unc, jets_var in jets_vars.iteritems():
    #        getattr(self.out,"njets_"+unc)[0] = len(jets_var)
    #        getattr(self.out,"ncjets_"+unc)[0] = ncjets_var
    #        getattr(self.out,"nfjets_"+unc)[0] = nfjets_var
    
    return jets, ht_muons, met, met_vars
    
  
  def fillCommonCorrBraches(self, event):
    """Help function to apply common corrections, and fill weight branches."""
    
    #if self.dorecoil:
    #  boson, boson_vis           = getBoson(event)
    #  self.recoilTool.CorrectPFMETByMeanResolution(met,boson,boson_vis,len(jets))
    #  self.out.m_moth[0]         = boson.M()
    #  self.out.pt_moth[0]        = boson.Pt()
    #  
    #  for unc in self.metUncLabels:
    #    self.recoilTool.CorrectPFMETByMeanResolution(met_vars[unc],boson,boson_vis,njets_vars.get(unc,len(jets)))
    #  
    #  if self.dozpt:
    #    self.out.zptweight[0]      = self.zptTool.getzptweight(boson.Pt(),boson.M())
    #

    if self.dozpt:
      zboson = getzboson(event)
      self.out.m_moth[0]      = zboson.M()
      self.out.pt_moth[0]     = zboson.Pt()
      self.out.zptweight[0]   = self.zptTool.getZptWeight(zboson.Pt(),zboson.M())
      
    elif self.dotoppt:
      toppt1, toppt2          = gettoppt(event)
      self.out.pt_moth1[0]    = max(toppt1,toppt2)
      self.out.pt_moth2[0]    = min(toppt1,toppt2)
      self.out.ttptweight[0]  = getTopPtWeight(toppt1,toppt2)
    
    if self.era=='UL2017':
      self.out.genweight[0]     = event.genWeight
    else:
      self.out.genweight[0]     = np.sign(event.genWeight)
    self.out.puweight[0]      = self.puTool.getWeight(event.Pileup_nTrueInt)

  # EXTRA TAU VETO
  def get_extratau_veto(self,event,leptons):
    tau_veto = False
    for tau in Collection(event,'Tau'):
      if tau.pt<20: continue
      if abs(tau.eta)>2.3: continue
      if abs(tau.dz)>0.2: continue
      if tau.decayMode not in [0,1,2,10,11]: continue
      if abs(tau.charge)!=1: continue
      if tau.idDeepTau2017v2p1VSe < 1 and tau.idDeepTau2018v2p5VSe < 1: continue   # VVVLoose
      if tau.idDeepTau2017v2p1VSmu < 1 and tau.idDeepTau2018v2p5VSmu < 1: continue  # VLoose
      overlap = False
      for lepton in leptons:
        if tau.DeltaR(lepton)<0.4:
          overlap = True
          break
      if overlap: continue          
      if tau.idDeepTau2017v2p1VSjet>=4 or tau.idDeepTau2018v2p5VSjet >=4: # Loose
        tau_veto = True
        break
    return tau_veto

  # EXTRA MUON VETO
  def get_extramuon_veto(self,event,leptons):
    muon_veto = False
    for muon in Collection(event,'Muon'):
      if muon.pt<10: continue
      if abs(muon.eta)>2.4: continue
      if abs(muon.dz)>0.2: continue
      if abs(muon.dxy)>0.045: continue
      if muon.pfRelIso04_all>0.3: continue
      overlap = False
      for lepton in leptons:
        if muon.DeltaR(lepton)<0.4:
          overlap = True
          break
      if overlap: continue
      if muon.mediumId:
        muon_veto = True
        break
    return muon_veto

  # EXTRA ELECTRON VETO
  def get_extraelec_veto(self,event,leptons):
    elec_veto = False
    for electron in Collection(event,'Electron'):
      if electron.pt<15: continue
      if abs(electron.eta)>2.5: continue
      if abs(electron.dz)>0.2: continue
      if abs(electron.dxy)>0.045: continue
      if electron.pfRelIso03_all>0.3: continue
      overlap = False
      for lepton in leptons:
        if electron.DeltaR(lepton)<0.4:
          overlap = True
          break
      if overlap: continue
      if electron.convVeto==1 and electron.mvaNoIso_WP80:
        elec_veto = True
        break
    return elec_veto

  def get_taujet(self,event,tau):
    jp4_match = TLorentzVector()
    jp4_match.SetPtEtaPhiM(tau.pt,tau.eta,tau.phi,tau.mass)
    jp4_genmatch = TLorentzVector()
    jp4_genmatch.SetPtEtaPhiM(tau.pt,tau.eta,tau.phi,tau.mass)
    if (tau.jetIdx>=0):
      jp4_match.SetPtEtaPhiM(event.Jet_pt[tau.jetIdx],
                             event.Jet_eta[tau.jetIdx],
                             event.Jet_phi[tau.jetIdx],
                             event.Jet_mass[tau.jetIdx])
      if self.ismc:
        if event.Jet_genJetIdx[tau.jetIdx]>=0:
          index = event.Jet_genJetIdx[tau.jetIdx]
          jp4_genmatch.SetPtEtaPhiM(event.GenJet_pt[index],
                                    event.GenJet_eta[index],
                                    event.GenJet_phi[index],
                                    event.GenJet_mass[index])
    return jp4_match,jp4_genmatch
