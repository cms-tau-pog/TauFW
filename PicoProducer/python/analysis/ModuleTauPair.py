# Author: Izaak Neutelings (June 2020)
# Description: Base class for ditau analyses
from ROOT import TFile, TTree
import sys, re
from math import sqrt, exp, cos
from ROOT import TLorentzVector, TVector3
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event
from TauFW.PicoProducer.corrections.PileupTool import *
from TauFW.PicoProducer.corrections.JetVetoMapTool import *
from TauFW.PicoProducer.corrections.RecoilCorrectionTool import *
#from TauFW.PicoProducer.corrections.PreFireTool import *
from TauFW.PicoProducer.corrections.BTagTool import BTagWeightTool, BTagWPs
from TauFW.common.tools.log import header
from TauFW.PicoProducer.analysis.utils import ensurebranches, redirectbranch, deltaPhi, getmet, getmetfilters, correctmet, getlepvetoes, filtermutau
__metaclass__ = type # to use super() with subclasses from CommonProducer
tauSFVersion  = { 2016: '2016Legacy', 2017: '2017ReReco', 2018: '2018ReReco', 2022: '2022ReReco' }



class ModuleTauPair(Module):
  """Base class the channels of an analysis with two tau leptons: for mutau, etau, tautau, emu, mumu, ee."""
  
  def __init__(self, fname, **kwargs):
    print(header(self.__class__.__name__))
    
    # SETTINGS
    self.filename   = fname # output file name
    self.dtype      = kwargs.get('dtype',    'data'         )
    self.ismc       = self.dtype=='mc'
    self.isdata     = self.dtype=='data' or self.dtype=='embed'
    self.isembed    = self.dtype=='embed'
    self.branchsel  = None # keep/drop file for branches: disable unneeded branches for faster processing
    self.channel    = kwargs.get('channel',  'none'         ) # channel name
    self.year       = kwargs.get('year',     2022           ) # integer, e.g. 2017, 2018
    self.era        = kwargs.get('era',      '2022postEE'   ) # string, e.g. '2017', 'UL2017'
    self.ees        = kwargs.get('ees',      1.0            ) # electron energy scale
    self.tes        = kwargs.get('tes',      None           ) # tau energy scale; if None, recommended values are applied
    self.tessys     = kwargs.get('tessys',   None           ) # vary TES: 'Up' or 'Down'
    self.fes        = kwargs.get('fes',      None           ) # electron-tau-fake energy scale: None, 'Up' or 'Down' (override with 'ltf=1')
    self.ltf        = kwargs.get('ltf',      None           ) # lepton-tau-fake energy scale
    self.jtf        = kwargs.get('jtf',      1.0            ) or 1.0 # jet-tau-fake energy scale
    ##addition Z resolution
    self.Zres       = kwargs.get('Zres',     None           ) # Z resolution 
    self.tauwp      = kwargs.get('tauwp',    1              ) # minimum DeepTau WP, e.g. 1 = VVVLoose, etc.
    self.dotoppt    = kwargs.get('toppt',    'TT' in fname  ) # top pT reweighting
    self.dozpt      = kwargs.get('zpt',      'DY' in fname  ) # Z pT reweighting
    self.domutau    = kwargs.get('domutau',  'DY' in fname or self.dozpt ) # mutau genfilter for stitching DY sample
    self.dopdf      = kwargs.get('dopdf',    False          ) and self.ismc # store PDF & scale weights
    self.dorecoil   = kwargs.get('recoil',   False          ) and self.ismc # recoil corrections #('DY' in name or re.search(r"W\d?Jets",name)) and self.year==2016) # and self.year==2016 
    self.dosys      = self.tessys in [None,''] and self.ltf in [1,None] and self.jtf in [1,None] # include systematic variations of weight
    self.dosys      = kwargs.get('sys',      self.dosys     ) # store fewer branches to save disk space
    self.dotight    = self.tes not in [1,None] or not self.dosys # tighten pre-selection to store fewer events
    self.dotight    = kwargs.get('tight',    self.dotight   ) # store fewer events to save disk space
    self.dojec      = kwargs.get('jec',      False          ) and self.ismc #and self.year==2016 #False
    self.dojecsys   = kwargs.get('jecsys',   self.dojec     ) and self.ismc and self.dosys #and self.dojec #and False
    self.useT1      = kwargs.get('useT1',    False          ) # MET T1 for backwards compatibility with old nanoAOD-tools JME corrector
    self.verbosity  = kwargs.get('verb',     0              ) # verbosity
    self.jetCutPt   = 30
    self.bjetCutEta = 2.4 if self.year==2016 else 2.5
    self.isUL       = 'UL' in self.era
    
    assert self.year in [2016,2017,2018,2022,2023,2024], "Did not recognize year %s! Please choose from 2016, 2017 and 2018."%self.year
    assert self.dtype in ['mc','data','embed'], "Did not recognize data type '%s'! Please choose from 'mc', 'data' and 'embed'."%self.dtype
    
    # YEAR-DEPENDENT IDs
    self.met        = getmet(self.era,"nom" if self.dojec else "",useT1=self.useT1,verb=self.verbosity)
    self.filter     = getmetfilters(self.era,self.isdata,verb=self.verbosity)
    
    # CORRECTIONS
    self.ismutau      = False # event passes gen mutau filter (to avoid computing twice)
    self.ptnom        = lambda j: j.pt # use 'pt' as nominal jet pt (not corrected)
    self.jecUncLabels = [ ]
    self.metUncLabels = [ ]
    if self.ismc:
      self.puTool      = PileupWeightTool(era=self.era,sample=self.filename,verb=self.verbosity)
      self.btagTool    = BTagWeightTool('DeepJet','medium',era=self.era,channel=self.channel,maxeta=self.bjetCutEta) #,loadsys=not self.dotight
      if self.dozpt:
        self.zptTool  = ZptCorrectionTool(era=self.era)
      #if self.dorecoil:
      #  self.recoilTool   = RecoilCorrectionTool(year=self.year)
      #if self.year in [2016,2017]:
      #  self.prefireTool  = PreFireTool(self.year)
      if self.dojec:
        self.ptnom = lambda j: j.pt_nom # use 'pt_nom' as nominal jet pt
      if self.dojecsys:
       self.jecUncLabels = [ u+v for u in ['JER','JES'] for v in ['Down','Up']]
       self.metUncLabels = [ u+v for u in ['JER','JES','Unclustered'] for v in ['Down','Up']]
       self.met_vars     = { u: getmet(self.era,u,useT1=self.useT1) for u in self.metUncLabels }
      #if self.isUL and self.tes==None:
      #  self.tes = 1.0 # placeholder
    self.jetvetoTool = None
    if '202' in self.era: # only mandatory for Run 3: 2022, 2023, ... (see https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps)
      self.jetvetoTool = JetVetoMapTool(era=self.era,verb=self.verbosity) 
    self.deepjet_wp = BTagWPs('DeepJet',era=self.era)
    
  
  def beginJob(self):
    """Before processing any events or files."""
    print('-'*80)
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
    #if self.channel.count('ele')>0:
    #  print ">>> %-12s = %s"%('ees',     self.ees)
    print(">>> %-12s = %s"%('dotoppt',   self.dotoppt))
    print(">>> %-12s = %s"%('dopdf',     self.dopdf))
    print(">>> %-12s = %s"%('dozpt',     self.dozpt))
    print(">>> %-12s = %s"%('domutau',   self.domutau))
    #print ">>> %-12s = %s"%('dorecoil',  self.dorecoil)
    print(">>> %-12s = %s"%('dojec',     self.dojec))
    print(">>> %-12s = %s"%('dojecsys',  self.dojecsys))
    print(">>> %-12s = %s"%('dosys',     self.dosys))
    print(">>> %-12s = %s"%('dotight',   self.dotight))
    print(">>> %-12s = %s"%('useT1',     self.useT1))
    print(">>> %-12s = %s"%('jetCutPt',  self.jetCutPt))
    print(">>> %-12s = %s"%('bjetCutEta',self.bjetCutEta))
    
  
  def endJob(self):
    """Wrap up after running on all events and files"""
    if self.ismc:
      self.btagTool.setDir(self.out.outfile,'btag')
    self.out.endJob()
    
  
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    """Before processing a new file."""
    sys.stdout.flush()

    # for v10
    branchesV10 = [
      ('Muon_isTracker',                  [True]*32     ),
      #('Electron_mvaFall17V217Iso',      [1.]*32       ), #not available anymore
      ('Electron_lostHits',               [0]*32        ),
      ('Electron_mvaFall17V2Iso_WPL',    'Electron_mvaIso_WPL'    ),
      ('Electron_mvaFall17V2Iso_WP80',   'Electron_mvaIso_WP80'   ),
      ('Electron_mvaFall17V2Iso_WP90',   'Electron_mvaIso_WP90'   ),
      ('Electron_mvaFall17V2noIso_WPL',  'Electron_mvaNoIso_WPL'  ),
      ('Electron_mvaFall17V2noIso_WP80', 'Electron_mvaNoIso_WP80' ),
      ('Electron_mvaFall17V2noIso_WP90', 'Electron_mvaNoIso_WP90' ),
      ('Tau_idDecayMode',                [True]*32               ), 
      ('Tau_idDecayModeNewDMs',          [True]*32               ),
      ('Tau_idDeepTau2018v2p5VSe','Tau_idDeepTau2017v2p1VSe'), 
      ('Tau_idDeepTau2018v2p5VSmu','Tau_idDeepTau2017v2p1VSmu'),  
      ('Tau_idDeepTau2018v2p5VSjet','Tau_idDeepTau2017v2p1VSjet'),
      ('Tau_rawDeepTau2018v2p5VSe','Tau_rawDeepTau2017v2p1VSe'), 
      ('Tau_rawDeepTau2018v2p5VSmu','Tau_rawDeepTau2017v2p1VSmu'),  
      ('Tau_rawDeepTau2018v2p5VSjet','Tau_rawDeepTau2017v2p1VSjet')
    ]
    # for v9
    branches = [
      ('Electron_mvaFall17V2Iso',        'Electron_mvaFall17Iso'        ),
      ('Electron_mvaFall17V2Iso_WPL',    'Electron_mvaFall17Iso_WPL'    ),
      ('Electron_mvaFall17V2Iso_WP80',   'Electron_mvaFall17Iso_WP80'   ),
      ('Electron_mvaFall17V2Iso_WP90',   'Electron_mvaFall17Iso_WP90'   ),
      ('Electron_mvaFall17V2noIso_WPL',  'Electron_mvaFall17noIso_WPL'  ),
      ('Electron_mvaFall17V2noIso_WP80', 'Electron_mvaFall17noIso_WP80' ),
      ('Electron_mvaFall17V2noIso_WP90', 'Electron_mvaFall17noIso_WP90' ),
      #('Flag_ecalBadCalibFilterV2',      True                           ),
      ('Tau_idDecayMode',                [True]*32                      ), # not available anymore in nanoAODv9
      ('Tau_idDecayModeNewDMs',          [True]*32                      ), # not available anymore in nanoAODv9
      #('Tau_rawAntiEle',                 [0.]*30                        ), #  # not available anymore in nanoAODv9
      #('Tau_rawMVAoldDM2017v2',          [0.]*30                        ), # not available anymore in nanoAODv9
      #('Tau_rawMVAnewDM2017v2',          [0.]*30                        ), # not available anymore in nanoAODv9
      ('Tau_idDeepTau2018v2p5VSe','Tau_idDeepTau2017v2p1VSe'), 
      ('Tau_idDeepTau2018v2p5VSmu','Tau_idDeepTau2017v2p1VSmu'),  
      ('Tau_idDeepTau2018v2p5VSjet','Tau_idDeepTau2017v2p1VSjet'),
      ('Tau_rawDeepTau2018v2p5VSe','Tau_rawDeepTau2017v2p1VSe'), 
      ('Tau_rawDeepTau2018v2p5VSmu','Tau_rawDeepTau2017v2p1VSmu'),  
      ('Tau_rawDeepTau2018v2p5VSjet','Tau_rawDeepTau2017v2p1VSjet')
    ]
    if self.year==2016:
      branches += [
        ('HLT_IsoMu22_eta2p1',   False ),
        ('HLT_IsoTkMu22_eta2p1', False ),
        ('HLT_IsoMu24',          False ),
        ('HLT_IsoTkMu24',        False ),
      ]
 
    #check
    fullbranchlist = inputTree.GetListOfBranches()
    if 'Electron_mvaFall17Iso_WPL' not in fullbranchlist: #v10
       ensurebranches(inputTree,branchesV10)
    else: #v9
       ensurebranches(inputTree,branches) # make sure Event object has these branches

  def jetveto(self, event):
    """Return number of vetoed jets. Jet veto maps are mandatory for Run 3 analyses.
    The safest procedure would be to veto events if ANY jet with a loose selection lies in the veto regions.
    See https://cms-jerc.web.cern.ch/Recommendations/#jet-veto-maps
    """
    if not self.jetvetoTool:
      return 0 # assume no jet veto required (e.g. for Run 2)
    vetojets = [ ]
    muons = [m for m in Collection(event,'Muon') if m.isPFcand]
    for jet in Collection(event,'Jet'):
      if abs(jet.pt) <= 15: continue
      if jet.jetId < 2: continue
      if (jet.chEmEF + jet.neEmEF) > 0.90: continue
      if not self.jetvetoTool.applyJetVetoMap(jet.eta, jet.phi): continue
      if any(jet.DeltaR(m)<0.2 for m in muons): continue # overlap
      vetojets.append(jet)
    return len(vetojets)

  def fillhists(self,event):
    """Help function to fill common histograms (cutflow etc.) before any cuts."""
    self.out.cutflow.fill('none')
    if self.isdata:
      self.out.cutflow.fill('weight',1.)
      if event.PV_npvs>0: # for pre-UL 2017 bug in 0 PU
        self.out.cutflow.fill('weight_no0PU',1.)
      else:
        return False
    else: # ismc
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
      if event.Pileup_nTrueInt>0: # for pre-UL 2017 bug in 0 PU
        self.out.cutflow.fill('weight_no0PU',event.genWeight)
      else: # bug in pre-UL 2017 caused small fraction of events with nPU<=0
        return False
      # Specific selections to compute mutau filter efficiencies for stitching of different DY samples (DYJetsToTauTauToMuTauh)
      if self.domutau:
        self.ismutau = filtermutau(event) # event passes gen mutau filter
        self.out.cutflow.fill('weight_mutaufilter',event.genWeight*self.ismutau)
        try:
          if event.LHE_Njets==0 or event.LHE_Njets>4:
            self.out.cutflow.fill('weight_mutaufilter_NUP0orp4',event.genWeight*self.ismutau)
          elif event.LHE_Njets==1:
            self.out.cutflow.fill('weight_mutaufilter_NUP1',event.genWeight*self.ismutau)
          elif event.LHE_Njets==2:
            self.out.cutflow.fill('weight_mutaufilter_NUP2',event.genWeight*self.ismutau)
          elif event.LHE_Njets==3:
            self.out.cutflow.fill('weight_mutaufilter_NUP3',event.genWeight*self.ismutau)
          elif event.LHE_Njets==4:
            self.out.cutflow.fill('weight_mutaufilter_NUP4',event.genWeight*self.ismutau)
        except RuntimeError:
          print(">>> WARNING: RuntimeError! Setting domutau=False !")
          self.domutau = False
      self.out.pileup.Fill(event.Pileup_nTrueInt)
    
    return True
    
  
  def fillEventBranches(self,event):
    """Help function to fill branches of common event variables."""
    
    # EVENT
    self.out.evt[0]             = event.event # ULong64_t -> uint64
    ###self.out.data[0]            = self.isdata # use setAlias instead
    self.out.run[0]             = event.run
    self.out.lumi[0]            = event.luminosityBlock
    self.out.npv[0]             = event.PV_npvs
    self.out.npv_good[0]        = event.PV_npvsGood
    self.out.metfilter[0]       = self.filter(event)
    
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
    ###elif self.isembed:
    ###  self.out.isdata[0]        = False
    
  
  def fillJetBranches(self,event,tau1,tau2):
    """Help function to select jets and b tags, after removing overlap with tau decay candidates,
    and fill the jet variable branches."""
    
    # NOMINAL AND VARIATIONS
    metnom     = self.met(event)
    met_vars   = { }
    if self.dojecsys:
      jets_vars = { u: [ ] for u in self.jecUncLabels }
      met_vars  = { u: self.met_vars[u](event) for u in self.metUncLabels } # TLVs
    
    # COUNTERS
    njets_vars     = { }
    jets,   bjets  = [ ], [ ]
    nfjets, ncjets = 0, 0
    ncjets50       = 0
    nbtag          = 0
    
    # SELECT JET, remove overlap with selected objects
    for jet in Collection(event,'Jet'):
      if abs(jet.eta)>4.7: continue
      if jet.DeltaR(tau1)<0.5: continue
      if jet.DeltaR(tau2)<0.5: continue
      if jet.jetId<2: continue # Tight
      
      # SAVE JEC VARIATIONS
      if self.dojec:
        jetpt = jet.pt_nom
        for unc in self.jecUncLabels:
          if getattr(jet,'pt_'+unc) < self.jetCutPt: continue
          jets_vars[unc].append(jet)
      else:
        jetpt = jet.pt
      
      # PT CUT
      if jetpt<self.jetCutPt: continue
      jets.append(jet)
      
      # COUNT FORWARD/CENTRAL
      if abs(jet.eta)>2.4:
        nfjets += 1
      else:
        ncjets += 1
        if jetpt>50:
          ncjets50 += 1
      
      # B TAGGING
      if jet.btagDeepFlavB>self.deepjet_wp.medium and abs(jet.eta)<self.bjetCutEta:
        nbtag += 1
        bjets.append(jet)
    
    #### TOTAL MOMENTUM
    ###eventSum = TLorentzVector()
    ###for lep in muons :
    ###    eventSum += lep.p4()
    ###for lep in electrons :
    ###    eventSum += lep.p4()
    ###for j in filter(self.jetSel,jets):
    ###    eventSum += j.p4()
    
    # FILL JET BRANCHES
    jets.sort( key=lambda j: self.ptnom(j),reverse=True)
    bjets.sort(key=lambda j: self.ptnom(j),reverse=True)
    self.out.njets[0]         = len(jets)
    self.out.njets50[0]       = len([j for j in jets if self.ptnom(j)>50])
    self.out.nfjets[0]        = nfjets
    self.out.ncjets[0]        = ncjets
    self.out.ncjets50[0]      = ncjets50
    self.out.nbtag[0]         = nbtag
    
    # LEADING JET
    if len(jets)>0:
      self.out.jpt_1[0]       = self.ptnom(jets[0])
      self.out.jeta_1[0]      = jets[0].eta
      self.out.jphi_1[0]      = jets[0].phi
      self.out.jdeepjet_1[0]  = jets[0].btagDeepFlavB
    else:
      self.out.jpt_1[0]       = -1.
      self.out.jeta_1[0]      = -9.
      self.out.jphi_1[0]      = -9.
      self.out.jdeepjet_1[0]  = -9.
    
    # SUBLEADING JET
    if len(jets)>1:
      self.out.jpt_2[0]       = self.ptnom(jets[1])
      self.out.jeta_2[0]      = jets[1].eta
      self.out.jphi_2[0]      = jets[1].phi
      self.out.jdeepjet_2[0]  = jets[1].btagDeepFlavB
    else:
      self.out.jpt_2[0]       = -1.
      self.out.jeta_2[0]      = -9.
      self.out.jphi_2[0]      = -9.
      self.out.jdeepjet_2[0]  = -9.
    
    # LEADING B JETS
    if len(bjets)>0:
      self.out.bpt_1[0]       = self.ptnom(bjets[0])
      self.out.beta_1[0]      = bjets[0].eta
    else:
      self.out.bpt_1[0]       = -1.
      self.out.beta_1[0]      = -9.
    
    # SUBLEADING B JETS
    if len(bjets)>1:
      self.out.bpt_2[0]       = self.ptnom(bjets[1])
      self.out.beta_2[0]      = bjets[1].eta
    else:
      self.out.bpt_2[0]       = -1.
      self.out.beta_2[0]      = -9.
    
    ## FILL JET VARIATION BRANCHES
    #if self.dojecsys:
    #  for unc, jets_var in jets_vars.items():
    #    ptvar = 'pt_'+unc
    #    jets_var.sort(key=lambda j: getattr(j,ptvar),reverse=True)
    #    njets_vars[unc] = len(jets_var)
    #    bjets_vars      = [j for j in jets_vars if j.btagDeepFlavB>self.deepjet_wp.medium and abs(j.eta)<self.bjetCutEta]
    #    getattr(self.out,"njets_"+unc)[0] = njets_vars[unc]
    #    getattr(self.out,"nbtag_"+unc)[0] = len(bjets_vars)
    #    getattr(self.out,"jpt_1_"+unc)[0] = getattr(jets_var[0],ptvar) if len(jets_var)>=1 else -1
    #    getattr(self.out,"jpt_2_"+unc)[0] = getattr(jets_var[1],ptvar) if len(jets_var)>=2 else -1
    
    return jets, metnom, njets_vars, met_vars
    
  
  def fillCommonCorrBranches(self, event, jets, met, njets_vars, met_vars):
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
    
    self.out.genweight[0]     = event.genWeight
    self.out.puweight[0]      = self.puTool.getWeight(event.Pileup_nTrueInt)
    self.out.btagweight[0]    = self.btagTool.getWeight(jets)
    if self.dosys:
      if self.dopdf:
        self.out.npdfweight[0]  = min(event.nLHEPdfWeight,len(self.out.pdfweight))
        for i in range(self.out.npdfweight[0]):
          self.out.pdfweight[i] = event.LHEPdfWeight[i]
        #self.out.muweight[0]          = event.LHEWeight_originalXWGTUP # scale weight, muR=1.0, muF=1.0
        #self.out.muweight_0p5_0p5[0]  = event.LHEScaleWeight[0] # scale weight, muR=0.5, muF=0.5 (rel.)
        #self.out.muweight_0p5_1p0[0]  = event.LHEScaleWeight[1] # scale weight, muR=0.5, muF=1.0 (rel.)
        #self.out.muweight_1p0_0p5[0]  = event.LHEScaleWeight[3] # scale weight, muR=1.0, muF=0.5 (rel.)
        #self.out.muweight_1p0_2p0[0]  = event.LHEScaleWeight[5] # scale weight, muR=1.0, muF=2.0 (rel.)
        #self.out.muweight_2p0_1p0[0]  = event.LHEScaleWeight[7] # scale weight, muR=2.0, muF=1.0 (rel.)
        #self.out.muweight_2p0_2p0[0]  = event.LHEScaleWeight[8] # scale weight, muR=2.0, muF=2.0 (rel.)
      #self.out.btagweight_bc[0],     self.out.btagweight_udsg[0]     = self.btagTool.getFlavorWeight(jets)
      #self.out.btagweight_bcUp[0],   self.out.btagweight_udsgUp[0]   = self.btagTool.getFlavorWeight(jets,unc='Up')
      #self.out.btagweight_bcDown[0], self.out.btagweight_udsgDown[0] = self.btagTool.getFlavorWeight(jets,unc='Down')
    #if self.year in [2016,2017]:
    #  self.out.prefireweightDown[0], self.out.prefireweight[0], self.out.prefireweightUp[0] = self.prefireTool.getWeight(event)
    
  
  def fillMETAndDiLeptonBranches(self, event, tau1, tau2, met, met_vars):
    """Help function to compute variable related to the MET and visible tau candidates,
     and fill the corresponding branches."""
    
    # PROPAGATE TES/LTF/JTF shift to MET (assume shift is already applied to object)
    if self.ismc and 't' in self.channel:
      if tau1.__dict__.get('es',1)!=1:
        #if hasattr(tau1,'es') and tau1.es!=1:
        dp = tau1.tlv*(1.-1./tau1.es) # assume shift is already applied
        correctmet(met,dp)
      if hasattr(tau2,'es') and tau2.es!=1:
        dp = tau2.tlv*(1.-1./tau2.es)
        #print ">>> fillMETAndDiLeptonBranches: Correcting MET for es=%.3f, pt=%.3f, dpt=%.3f, gm=%d"%(tau2.es,tau2.pt,dp.Pt(),tau2.genPartFlav)
        correctmet(met,tau2.tlv*(1.-1./tau2.es))
    tau1 = tau1.tlv # continue with TLorentzVector
    tau2 = tau2.tlv # continue with TLorentzVector
    
    # MET
    self.out.met[0]       = met.Pt()
    self.out.metphi[0]    = met.Phi()
    self.out.mt_1[0]      = sqrt( 2*self.out.pt_1[0]*met.Pt()*(1-cos(deltaPhi(self.out.phi_1[0],met.Phi()))) )
    self.out.mt_2[0]      = sqrt( 2*self.out.pt_2[0]*met.Pt()*(1-cos(deltaPhi(self.out.phi_2[0],met.Phi()))) )
    ###self.out.puppimetpt[0]             = event.PuppiMET_pt
    ###self.out.puppimetphi[0]            = event.PuppiMET_phi
    ###self.out.metsignificance[0]        = event.MET_significance
    ###self.out.metcov00[0]               = event.MET_covXX
    ###self.out.metcov01[0]               = event.MET_covXY
    ###self.out.metcov11[0]               = event.MET_covYY
    ###self.out.fixedGridRhoFastjetAll[0] = event.fixedGridRhoFastjetAll
    
    # PZETA
    leg1                  = TVector3(tau1.Px(),tau1.Py(),0.)
    leg2                  = TVector3(tau2.Px(),tau2.Py(),0.)
    zetaAxis              = TVector3(leg1.Unit()+leg2.Unit()).Unit() # bisector of visible tau candidates
    pzetavis              = leg1*zetaAxis + leg2*zetaAxis # bisector of visible ditau momentum onto zeta axis
    pzetamiss             = met.Vect()*zetaAxis # projection of MET onto zeta axis
    self.out.pzetamiss[0] = pzetamiss
    self.out.pzetavis[0]  = pzetavis
    self.out.dzeta[0]     = pzetamiss - 0.85*pzetavis
    
    # MET SYSTEMATICS
    for unc, met_var in met_vars.items():
      getattr(self.out,"met_"+unc)[0]    = met_var.Pt()
      getattr(self.out,"metphi_"+unc)[0] = met_var.Phi()
      getattr(self.out,"mt_1_"+unc)[0]   = sqrt( 2 * self.out.pt_1[0] * met_var.Pt() * ( 1 - cos(deltaPhi(self.out.phi_1[0],met_var.Phi())) ))
      getattr(self.out,"dzeta_"+unc)[0]  = met_var.Vect()*zetaAxis - 0.85*pzeta_vis
    
    # DILEPTON
    self.out.m_vis[0]     = (tau1 + tau2).M()
    self.out.pt_ll[0]     = (tau1 + tau2).Pt()
    self.out.dR_ll[0]     = tau1.DeltaR(tau2)
    self.out.dphi_ll[0]   = deltaPhi(self.out.phi_1[0], self.out.phi_2[0])
    self.out.deta_ll[0]   = abs(self.out.eta_1[0] - self.out.eta_2[0])
    self.out.chi[0]       = exp(abs(tau1.Rapidity() - tau2.Rapidity()))
    
