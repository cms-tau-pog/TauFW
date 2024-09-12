# Author: Izaak Neutelings (May 2020)
#from __future__ import print_function # for python3 compatibility
import os, sys
from math import sqrt, sin, cos, pi, log10, floor
from itertools import combinations
import ROOT; ROOT.PyConfig.IgnoreCommandLineOptions = True # to avoid conflict with argparse
from ROOT import TH1D, TLorentzVector, RDataFrame
from TauFW.PicoProducer import basedir
from TauFW.common.tools.utils import getyear, convertstr # for picojob.py
from TauFW.common.tools.file import ensurefile
from TauFW.common.tools.file import ensuremodule as _ensuremodule
from TauFW.common.tools.log import Logger
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Event, Object
LOG = Logger('Analysis')


statusflags_dict = { # GenPart_statusFlags, stored bitwise:
  # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
  'isPrompt':                      0,   'fromHardProcess':                     8,
  'isDecayedLeptonHadron':         1,   'isHardProcessTauDecayProduct':        9,
  'isTauDecayProduct':             2,   'isDirectHardProcessTauDecayProduct': 10,
  'isPromptTauDecayProduct':       3,   'fromHardProcessBeforeFSR':           11,
  'isDirectTauDecayProduct':       4,   'isFirstCopy':                        12,
  'isDirectPromptTauDecayProduct': 5,   'isLastCopy':                         13,
  'isDirectHadronDecayProduct':    6,   'isLastCopyBeforeFSR':                14,
  'isHardProcess':                 7,
}


def ensuremodule(modname):
  """Check if module exists and has class of same name."""
  if ' ' in modname:
    modname = modname.split(' ')[0]
  return _ensuremodule(modname,"PicoProducer.analysis")
  

def getmodule(modname):
  """Get give module from python module in python/analysis of the same name."""
  if ' ' in modname:
    modname = modname.split(' ')[0]
  module   = ensuremodule(modname)  # e.g. PicoProducer.analysis.ModuleMuTau
  modclass = modname.split('.')[-1] # e.g. ModuleMuTau
  return getattr(module,modclass)
  

def ensurebranches(tree,branches):
  """Check if these branches are available in the tree branch list,
  if not, redirect them."""
  if tree.GetEntries()<1:
    print("WARNING! Empty tree!")
    return
  fullbranchlist = tree.GetListOfBranches()
  for newbranch, oldbranch in branches:
    if newbranch not in fullbranchlist:
      redirectbranch(oldbranch,newbranch)
  

def redirectbranch(oldbranch,newbranch):
  """Redirect some branch names. newbranch -> oldbranch"""
  if isinstance(oldbranch,str): # rename
    print("redirectbranch: directing %r -> %r"%(newbranch,oldbranch))
    exec("setattr(Event,newbranch,property(lambda self: self._tree.readBranch(%r)))"%(oldbranch))
  else: # set default value
    print("redirectbranch: directing %r -> %r"%(newbranch,oldbranch))
    exec("setattr(Event,newbranch,%s)"%(oldbranch))
  

def hasbit(value,bit):
  """Check if i'th bit is set to 1, i.e. binary of 2^i,
  from the right to the left, starting from position i=0."""
  ###return bin(value)[-bit-1]=='1'
  ###return format(value,'b').zfill(bit+1)[-bit-1]=='1'
  return (value & (1 << bit))>0
  

def hasstatusflag(particle,*flags):
  """Check if status flag of a GenPart is set."""
  # https://cms-nanoaod-integration.web.cern.ch/integration/master-102X/mc102X_doc.html#GenPart
  # Alternatively, use Object.statusflag("flag"):
  # https://github.com/cms-nanoAOD/nanoAOD-tools/blob/master/python/postprocessing/framework/datamodel.py
  return all((particle.statusFlags & (1 << statusflags_dict[f]))>0 for f in flags)
#Object.statusflag = hasstatusflag # promote to method of Object class for GenPart
# See PR: https://github.com/cms-nanoAOD/nanoAOD-tools/pull/301


def dumpgenpart(part,genparts=None,event=None,flags=[],bits=[],grand=False):
  """Print information on gen particle. If collection is given, also print mother's PDG ID."""
  info = ">>>  i=%2s, PID=%3s, status=%2s, mother=%2s"%(part._index,part.pdgId,part.status,part.genPartIdxMother)
  if part.genPartIdxMother>=0:
    if genparts: 
      moth  = genparts[part.genPartIdxMother]
      info += " (%3s)"%(moth.pdgId)
      if grand and moth.genPartIdxMother>=0:
        grand = genparts[moth.genPartIdxMother]
        info += ", grand=%2s (%3s)"%(moth.genPartIdxMother, grand.pdgId)
    elif event:
      moth  = part.genPartIdxMother
      info += " (%3s)"%(event.GenPart_pdgId[moth])
      if grand and event.GenPart_genPartIdxMother[moth]>=0:
        granid = event.GenPart_genPartIdxMother[moth]
        info  += ", grand=%2s (%3s)"%(event.GenPart_genPartIdxMother[granid],event.GenPart_pdgId[granid])
  for flag in flags:
    info += ", %s=%r"%(flag,part.statusflag(flag))
  for bit in bits:
    info += ", bit%s=%d"%(bit,hasbit(part.statusFlags,bit))
  print(info)
  

def getmother(part,genparts):
  """Get mother (which is not itself."""
  moth = part
  while moth.genPartIdxMother>=0 and part.pdgId==moth.pdgId:
    moth = genparts[moth.genPartIdxMother]
  return moth
  

def getlastcopy(part,genparts):
  """Get last copy, e.g. after all initial/final state radiation."""
  moth  = part
  imoth = part._index # index of mother in GenPart collection
  for idau in range(part._index+1,len(genparts)): # assume indices are chronologically ordered
    if moth.statusflag('isLastCopy'):
      ###print(f">>> getlastcopy: moth={moth} with i={moth._index}, pid={moth.pdgId} is last copy: break")
      break # assume no more copies
    dau = genparts[idau]
    ###print(f">>> getlastcopy: moth={moth} with i={moth._index}, pid={moth.pdgId}, dau={dau} with i={idau}, pid={dau.pdgId}, imoth={dau.genPartIdxMother}")
    if dau.pdgId==moth.pdgId and (dau.genPartIdxMother==moth._index): #or dau.genPartIdxMother==part._index):
      moth = dau # assume daughter is copy of mother
  ###else: # no break in for-loop
  ###  print(f">>> getlastcopy: no break")
  return moth
  

def getprodchain(part,genparts=None,event=None):
  """Return string of productions chain."""
  chain = "%3s"%(part.pdgId)
  imoth = part.genPartIdxMother # index of mother in GenPart collection
  while imoth>=0:
    if genparts:
      moth = genparts[imoth]
      chain = "%3s -> "%(moth.pdgId)+chain
      imoth = moth.genPartIdxMother
    elif event:
      chain = "%3s -> "%(event.GenPart_pdgId[imoth])+chain
      imoth = event.GenPart_genPartIdxMother[imoth]
    else:
      raise IOError("getprodchain: genparts or event must be defined")
  return chain
  

def getdecaychain(part,genparts,indent=0):
  """Print decay chain."""
  chain   = "%3s"%(part.pdgId)
  imoth   = part._index # index of mother in GenPart collection
  ndaus   = 0
  indent_ = len(chain)+indent
  for idau in range(imoth+1,len(genparts)): # assume indices are chronologically ordered
    dau = genparts[idau]
    if dau.genPartIdxMother==imoth:
      if ndaus>=1:
        chain += '\n'+' '*indent_
      chain += " -> "+getdecaychain(dau,genparts,indent=indent_+4)
      ndaus += 1
  return chain
  

def filtermutau(event):
  """Filter mutau final state with mu pt>18, |eta|<2.5 and tauh pt>18, |eta|<2.5
  to find overlap between DYJetsToLL_M-50 and DYJetsToTauTauToMuTauh_M-50 for stitching.
  Efficiency: ~70.01% for DYJetsToTauTauToMuTauh_M-50, ~0.774% for DYJetsToLL_M-50.
  
  Pythia8 gen filter with ~2.57% efficiency for DYJetsToTauTauToMuTauh:
    MuHadCut = cms.string('Mu.Pt > 16 && Had.Pt > 16 && Mu.Eta < 2.5 && Had.Eta < 2.7')
    https://cms-pdmv.cern.ch/mcm/edit?db_name=requests&prepid=TAU-RunIISummer19UL18wmLHEGEN-00007
    https://github.com/cms-sw/cmssw/blob/master/GeneratorInterface/Core/src/EmbeddingHepMCFilter.cc
  Pythia8 gen filter bug fix:
    https://github.com/cms-sw/cmssw/pull/38829
    https://indico.cern.ch/event/1170879/#2-validation-of-exclusive-dy-t
  """
  ###print '-'*80
  particles = Collection(event,'GenPart')
  muon = None
  taus = [ ]
  ###hasZ = False # Z boson required in the buggy DYJetsToTauTauToMuTauh Pythia8 filter
  for particle in particles:
    pid = abs(particle.pdgId)
    if pid==13 and (particle.statusflag('isHardProcessTauDecayProduct') or particle.statusflag('isDirectHardProcessTauDecayProduct')):
      ###dumpgenpart(particle,genparts=particles,flags=[3,4,5,6,8,9,10])
      if muon: # more than two muons from hard-proces taus
        return False # do not bother any further
      muon = particle
    elif pid==15 and particle.statusflag('fromHardProcess'): # status==2 = last copy
      if particle.status==2:
        ###print getprodchain(particle,particles)
        particle.pvis = TLorentzVector() # visible 4-momentum
        taus.append(particle)
      ###else: # particle.status==23
      ###  # QUICK FIX to exclude events with taus radiating FSR photons due to bug in EmbeddingHepMCFilter
      ###  # pre-CMSSW_10_6_30_patch1 affecting Summer19 and Summer20 UL
      ###  # => loss of ~20% events in DYJetsToTauTauToMuTauh
      ###  ###dumpgenpart(particle,genparts=particles,flags=['fromHardProcess','isHardProcessTauDecayProduct','isDirectHardProcessTauDecayProduct','isLastCopy'])
      ###  ###print(getdecaychain(particle,particles))
      ###  return False # veto events with radiating taus !
    ###elif pid==23:
    ###  hasZ = True # Z boson required in buggy DYJetsToTauTauToMuTauh Pythia8 filter
    elif pid>16: # ignore neutrinos and charged leptons
      for tau in taus:
        if tau._index==particle.genPartIdxMother: # non-leptonic tau decay product
          ###print(">>> add %+d to %+d"%(particle.pdgId,tau.pdgId))
          tau.pvis += particle.p4() # add visible tau decay product
  if len(taus)==2 and muon and muon.pt>18. and abs(muon.eta)<2.5:
    if any(tau.pdgId*muon.pdgId<0 and tau.pvis.Pt()>18 and abs(tau.pvis.Eta())<2.5 for tau in taus):
      return True
  ###for genvistau in Collection(event,'GenVisTau'): # not complete...
  ###  ###print ">>> genvistau: pt=%.1f, eta=%.2f"%(genvistau.pt,genvistau.eta)
  ###  if genvistau.pt>18 and abs(genvistau.eta)<2.5 and genvistau.charge*muon.pdgId>0: #and any(genvistau.DeltaR(t)<0.5 for t in taus)
  ###    return True
  return False
  

def matchgenvistau(event,tau,dRmin=0.5):
  """Help function to match tau object to gen vis tau."""
  # TO CHECK:
  #genvistau_idx = tau.genPartIdx
  #if genvistau_idx > -1:
  #  return event.GenVisTau_pt[genvistau_idx], event.GenVisTau_eta[genvistau_idx], event.GenVisTau_phi[genvistau_idx], event.GenVisTau_status[genvistau_idx]
  #else:
  #  return -1, -9, -9, -1
  taumatch = None
  for genvistau in Collection(event,'GenVisTau'):
    dR = genvistau.DeltaR(tau)
    if dR<dRmin:
      dRmin    = dR
      taumatch = genvistau
  if taumatch:
    return taumatch.pt, taumatch.eta, taumatch.phi, taumatch.status
  else:
    return -1, -9, -9, -1
  

def matchtaujet(event,tau,ismc):
  """Help function to match tau object to (gen) jet."""
  jpt_match    = -1
  jpt_genmatch = -1
  if tau.jetIdx>=0:
    jpt_match = event.Jet_pt[tau.jetIdx]
    if ismc:
      if event.Jet_genJetIdx[tau.jetIdx]>=0:
        jpt_genmatch = event.GenJet_pt[event.Jet_genJetIdx[tau.jetIdx]]
  return jpt_match, jpt_genmatch
  

def deltaR(eta1, phi1, eta2, phi2):
  """Compute DeltaR."""
  deta = eta1 - eta2
  dphi = deltaPhi(phi1, phi2)
  return sqrt( deta*deta + dphi*dphi )
  

def deltaPhi(phi1, phi2):
  """Computes DeltaPhi, handling periodic limit conditions."""
  res = phi1 - phi2
  while res>pi:
    res -= 2*pi
  while res<-pi:
    res += 2*pi
  return res
  

def getmet(era,var="",useT1=False,verb=0):
  """Return year-dependent MET recipe."""
  if not isinstance(era,str):
    LOG.warn(">>> getmet: Got era=%r (type==%s), but expected string! Converting..."%(era,type(era)))
    era = str(era)
  if '2017' in era and 'UL' not in era :
    branch  = 'METFixEE2017'
  elif '2022' in era or '2023' in era:
    branch = 'PuppiMET'
  else :
    branch = 'MET'
  #branch  = 'METFixEE2017' if ('2017' in era and 'UL' not in era) else 'MET'
  if useT1 and 'unclustEn' not in var:
    branch += "_T1"
    if var=='nom':
      var = ""
  pt  = '%s_pt'%(branch)
  phi = '%s_phi'%(branch)
  if var:
    pt  += '_'+var
    phi += '_'+var
  funcstr = "lambda e: TLorentzVector(e.%s*cos(e.%s),e.%s*sin(e.%s),0,e.%s)"%(pt,phi,pt,phi,pt)
  if verb>=1:
    LOG.verb(">>> getmet: %r"%(funcstr))
  print(">>> getmet: %r"%(funcstr))
  return eval(funcstr)
  

def correctmet(met,dp):
  """Correct the MET by removing a four-vector, ensuring the MET has no z component or mass component.""" 
  met -= dp
  met.SetPxPyPzE(met.Px(),met.Py(),0,sqrt(met.Px()**2+met.Py()**2))
  return met
  

def getmetfilters(era,isdata,verb=0):
  """Return a method to check if an event passes the recommended MET filters."""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2
  #if '2017' in era or '2018' in era:
  #  if isdata:
  #    return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
  #                     e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_eeBadScFilter and e.Flag_ecalBadCalibFilterV2
  #  else:
  #    return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
  #                     e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_ecalBadCalibFilterV2 # eeBadScFilter "not suggested"
  #else:
  #  if isdata:
  #    return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
  #                     e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_eeBadScFilter
  #  else:
  #    return lambda e: e.Flag_goodVertices and e.Flag_globalSuperTightHalo2016Filter and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
  #                     e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter # eeBadScFilter "not suggested"
  filters = [
    'Flag_goodVertices',
    'Flag_globalSuperTightHalo2016Filter',
    'Flag_HBHENoiseFilter',
    'Flag_HBHENoiseIsoFilter',
    'Flag_eeBadScFilter',
    'Flag_EcalDeadCellTriggerPrimitiveFilter',
    'Flag_BadPFMuonFilter',
  ]
  if isdata:
    filters.extend(['Flag_eeBadScFilter']) # eeBadScFilter "not suggested" for MC
  if ('2017' in era or '2018' in era) and ('UL' not in era):
    filters.extend(['Flag_ecalBadCalibFilterV2']) # under review for change in Ultra Legacy
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2#Run_2_recommendations
  if '2022' in era or '2023' in era: 
    filters.extend(['Flag_BadPFMuonDzFilter'])
    filters.extend(['Flag_hfNoisyHitsFilter'])
    filters.extend(['Flag_eeBadScFilter'])
    filters.extend(['Flag_ecalBadCalibFilter'])
    filters.remove('Flag_HBHENoiseFilter')
    filters.remove('Flag_HBHENoiseIsoFilter')
  

  funcstr = "lambda e: e."+' and e.'.join(filters)
  if verb>=1:
    LOG.verb(">>> getmetfilters: %r"%(funcstr))
  print(">>> getmetfilters: %r"%(funcstr))
  return eval(funcstr)
  

def loosestIso(tau):
  """Return a method to check whether event passes the VLoose working
  point of all available tau IDs. (For tau ID measurement.)"""
  return tau.idDeepTau2017v2p1VSjet>=2 # VVLoose
  #ord(e.Tau_idMVAnewDM2017v2[i])>0 or ord(e.Tau_idMVAoldDM2017v2[i])>0
  #ord(e.Tau_idMVAoldDM[i])>0 or ord(e.Tau_idMVAoldDM2017v1[i])>0
  

def idIso(tau):
  """Compute WPs of cut-based tau isolation."""
  raw = tau.rawIso
  if tau.photonsOutsideSignalCone/tau.pt<0.10:
    return 0 if raw>4.5 else 1 if raw>3.5 else 3 if raw>2.5 else 7 if raw>1.5 else 15 if raw>0.8 else 31 # VVLoose, VLoose, Loose, Medium, Tight
  return 0 if raw>4.5 else 1 if raw>3.5 else 3 # VVLoose, VLoose


def getlepvetoes(event, electrons, muons, taus, channel, era):
  """Check if event has extra electrons or muons. (HTT definitions.)"""
  # https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauWorkingLegacyRun2#Common_lepton_vetoes
  
  extramuon_veto = False
  extraelec_veto = False
  dilepton_veto  = False
  
  # EXTRA MUON VETO
  looseMuons = [ ]
  for muon in Collection(event,'Muon'):
    if muon.pt<10: continue
    if abs(muon.eta)>2.4: continue
    if abs(muon.dz)>0.2: continue
    if abs(muon.dxy)>0.045: continue
    if muon.pfRelIso04_all>0.3: continue
    if any(muon.DeltaR(tau)<0.4 for tau in taus): continue
    if muon.mediumId and all(m._index!=muon._index for m in muons):
      extramuon_veto = True
    if muon.pt>15 and muon.isPFcand and muon.isGlobal and muon.isTracker:
      looseMuons.append(muon)


  # EXTRA ELECTRON VETO
  looseElectrons = [ ]
  for electron in Collection(event,'Electron'): 
    if '2022' in era:
      electronIso90=electron.mvaIso_Fall17V2_WP90
      electronIso=electron.mvaIso_Fall17V2_WPL
    elif '2023' in era:
      electronIso90=electron.mvaIso_WP90
      electronIso=electron.mvaIso
    else:
      electronIso90=electron.mvaFall17V2Iso_WP90
      electronIso=electron.mvaFall17V2Iso_WPL

    if electron.pt<10: continue
    if abs(electron.eta)>2.5: continue
    if abs(electron.dz)>0.2: continue
    if abs(electron.dxy)>0.045: continue
    if electron.pfRelIso03_all>0.3: continue
    if any(electron.DeltaR(tau)<0.4 for tau in taus): continue
    if all(e._index!=electron._index for e in electrons) and electron.convVeto==1 and electron.lostHits<=1 and electronIso90:
      extraelec_veto = True
    if electron.pt>15 and electron.cutBased>0 and electronIso:
      looseElectrons.append(electron)
 
  # DILEPTON VETO
  if channel=='mutau':
    for muon1, muon2 in combinations(looseMuons,2):
      if muon1.charge*muon2.charge<0 and muon1.DeltaR(muon2)>0.15:
        dilepton_veto = True
        break
  elif channel=='eletau' or channel=='etau':
    for electron1, electron2 in combinations(looseElectrons,2):
      if electron1.charge*electron2.charge<0 and electron1.DeltaR(electron2)>0.20:
        dilepton_veto = True
        break
  
  return extramuon_veto, extraelec_veto, dilepton_veto
  

class LeptonPair:
  """Container class to pair and order tau decay candidates."""
  def __init__(self, obj1, iso1, obj2, iso2):
    self.obj1 = obj1
    self.obj2 = obj2
    self.pt1  = obj1.pt
    self.pt2  = obj2.pt
    self.iso1 = iso1
    self.iso2 = iso2
    self.pair = [obj1,obj2]
  
  def __gt__(self, opair):
    """Order dilepton pairs according to the pT of both objects first, then in isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 < opair.iso1 # greater = smaller isolation
    elif self.iso2 != opair.iso2: return self.iso2 < opair.iso2 # greater = smaller isolation
    return True
  
class LeptonTauPair(LeptonPair):
  def __gt__(self, opair):
    """Override for tau isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 < opair.iso1 # greater = smaller lepton isolation
    elif self.iso2 != opair.iso2: return self.iso2 > opair.iso2 # greater = larger tau isolation
    return True
  
class DiTauPair(LeptonPair):
  def __gt__(self, opair):
    """Override for tau isolation."""
    if   self.pt1  != opair.pt1:  return self.pt1  > opair.pt1  # greater = higher pT
    elif self.pt2  != opair.pt2:  return self.pt2  > opair.pt2  # greater = higher pT
    elif self.iso1 != opair.iso1: return self.iso1 > opair.iso1 # greater = larger tau isolation
    elif self.iso2 != opair.iso2: return self.iso2 > opair.iso2 # greater = larger tau isolation
    return True
  
def getTotalWeight(file, selections=[""]):
  # This function was proposed by Konstantin Androsov to solve the problem with normalization of WJets. It should work also for skimmed data
  # Allow to define (truth level) cuts to compute sum weight for given phase space -- needed for stitching ; giving list of different selection scenarios to compute
    total_w = []
    for tree_name in [ 'Events', 'EventsNotSelected' ]:
        df = RDataFrame(tree_name, file)
        df = df.Define('genWeightD', 'std::copysign<double>(1., genWeight)')
        for iSel, sel in enumerate(selections):
          if len(sel)>0:
            dfTemp = df.Filter(sel)
            w = dfTemp.Sum('genWeightD')
          else:
            w = df.Sum('genWeightD')
        total_w[iSel] += w.GetValue()
    return total_w
  
def getNevt(file): #This function extracts the number of events form Data files
  df = RDataFrame('Events', file)
  count_result = df.Count()
  return count_result.GetValue()
